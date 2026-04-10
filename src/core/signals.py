"""Сигналы движка — связь между ядром и интерфейсом."""

from PyQt5.QtCore import QObject, pyqtSignal


class EngineSignals(QObject):
    """Qt-сигналы для обновления UI из потока хука."""

    progress_changed = pyqtSignal(int, int)  # (текущая позиция, всего символов)
    char_typed = pyqtSignal(str)             # какой символ напечатан
    toggled = pyqtSignal(bool)               # вкл/выкл печати
    finished = pyqtSignal()                  # весь код набран
