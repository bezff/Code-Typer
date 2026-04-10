"""
Ядро перехвата клавиш через Win32 low-level keyboard hook (ctypes).

Используем флаг LLKHF_INJECTED чтобы отличить реальные нажатия
от наших собственных SendInput — единственный надёжный способ на Windows.
"""

import ctypes
import ctypes.wintypes as wt
import threading
import time
from typing import Optional

from .signals import EngineSignals

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Win32 константы
WH_KEYBOARD_LL = 13
HC_ACTION = 0

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

LLKHF_INJECTED = 0x00000010

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_F6 = 0x75
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_CONTROL = 0x11

# модификаторы и системные клавиши — всегда пропускаем
_PASSTHROUGH_VKS = frozenset({
    0x10, 0x11, 0x12,                       # Shift, Ctrl, Alt
    0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5,   # левый/правый Shift, Ctrl, Alt
    0x5B, 0x5C,                             # Win
    0x14, 0x90, 0x91,                       # CapsLock, NumLock, ScrollLock
    0x2C, 0x13,                             # PrintScreen, Pause
    0x70, 0x71, 0x72, 0x73, 0x74,           # F1–F5
    0x76, 0x77, 0x78, 0x79, 0x7A, 0x7B,    # F7–F12
    0x1B,                                   # Escape
})

# Win32 структуры


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.c_ulong),
        ("scanCode", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MOUSEINPUT(ctypes.Structure):
    """Нужна чтобы размер INPUT совпадал с Win32 layout."""
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUTunion)]


HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wt.WPARAM, wt.LPARAM,
)

# вспомогательные функции ввода

_INPUT_SIZE = ctypes.sizeof(INPUT)


def _send_vk(vk: int) -> None:
    """Нажать и отпустить виртуальную клавишу через SendInput."""
    inputs = (INPUT * 2)()
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki.wVk = vk
    inputs[0].union.ki.dwFlags = 0
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].union.ki.wVk = vk
    inputs[1].union.ki.dwFlags = KEYEVENTF_KEYUP
    user32.SendInput(2, inputs, _INPUT_SIZE)


def _send_unicode(char: str) -> None:
    """Отправить юникод-символ через SendInput."""
    code = ord(char)
    inputs = (INPUT * 2)()
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki.wScan = code
    inputs[0].union.ki.dwFlags = KEYEVENTF_UNICODE
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].union.ki.wScan = code
    inputs[1].union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
    user32.SendInput(2, inputs, _INPUT_SIZE)


class CodeTyperEngine:
    """Ядро: перехватывает нажатия и печатает загруженный код."""

    def __init__(self, toggle_vk: int = VK_F6) -> None:
        self._code: str = ""
        self._pos: int = 0
        self._active: bool = False
        self._toggle_vk: int = toggle_vk
        self._delay: float = 0.0
        self._next_time: float = 0.0
        self._hook_id = None
        self._hook_thread: Optional[threading.Thread] = None
        self._hook_tid: int = 0
        self._hook_ref = None  # prevent GC of ctypes callback
        self._lock = threading.Lock()
        self.signals = EngineSignals()

    # публичное API

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        with self._lock:
            self._code = value
            self._pos = 0
        self.signals.progress_changed.emit(0, len(value))

    @property
    def position(self) -> int:
        return self._pos

    @property
    def total(self) -> int:
        return len(self._code)

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def delay(self) -> float:
        return self._delay

    @delay.setter
    def delay(self, value: float) -> None:
        self._delay = max(0.0, value)

    def reset(self) -> None:
        with self._lock:
            self._pos = 0
        self.signals.progress_changed.emit(0, len(self._code))

    def toggle(self) -> None:
        self._active = not self._active
        self.signals.toggled.emit(self._active)

    def start_listener(self) -> None:
        if self._hook_thread is not None:
            return
        self._hook_thread = threading.Thread(target=self._pump, daemon=True)
        self._hook_thread.start()

    def stop_listener(self) -> None:
        if self._hook_thread is None:
            return
        if self._hook_tid:
            user32.PostThreadMessageW(self._hook_tid, WM_QUIT, 0, 0)
        self._hook_thread.join(timeout=2.0)
        self._hook_thread = None
        self._hook_tid = 0
        self._active = False
        self.signals.toggled.emit(False)

    # поток хука

    def _pump(self) -> None:
        """Ставим хук и крутим Windows message pump."""
        self._hook_tid = kernel32.GetCurrentThreadId()
        self._hook_ref = HOOKPROC(self._ll_handler)
        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._hook_ref, None, 0,
        )
        try:
            msg = wt.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._hook_id:
                user32.UnhookWindowsHookEx(self._hook_id)
                self._hook_id = None

    def _ll_handler(self, nCode: int, wParam: int, lParam: int) -> int:
        """Колбэк низкоуровневого клавиатурного хука."""
        if nCode != HC_ACTION:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

        # наши собственные инъекции — пропускаем
        if kb.flags & LLKHF_INJECTED:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        vk = kb.vkCode
        is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)

        # F6 переключает режим, глушим и нажатие и отпускание
        if vk == self._toggle_vk:
            if is_down:
                self.toggle()
            return 1

        # модификаторы и системные — пропускаем
        if vk in _PASSTHROUGH_VKS:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Alt-комбинации пропускаем
        if wParam in (WM_SYSKEYDOWN, WM_SYSKEYUP):
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Ctrl-комбинации пропускаем
        if user32.GetAsyncKeyState(VK_CONTROL) & 0x8000:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # не активен — пропускаем
        if not self._active:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # глушим отпускание клавиш пока активны
        if not is_down:
            return 1

        # ограничение скорости по настройке задержки
        now = time.perf_counter()
        if self._delay > 0 and now < self._next_time:
            return 1

        # печатаем следующий символ из кода
        with self._lock:
            if self._pos >= len(self._code):
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            char = self._code[self._pos]
            self._pos += 1
            pos_snap = self._pos

        self._type_char(char)

        if self._delay > 0:
            self._next_time = time.perf_counter() + self._delay

        self.signals.char_typed.emit(char)
        self.signals.progress_changed.emit(pos_snap, len(self._code))

        if pos_snap >= len(self._code):
            self.signals.finished.emit()

        return 1  # глушим оригинальную клавишу

    def _type_char(self, char: str) -> None:
        if char == "\n":
            _send_vk(VK_RETURN)
        elif char == "\t":
            _send_vk(VK_TAB)
        else:
            _send_unicode(char)
