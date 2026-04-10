"""Светлая тема оформления приложения."""

# основные цвета
_WHITE      = "#ffffff"
_BG         = "#f5f5f7"
_CARD_BG    = "#ffffff"
_BORDER     = "#d1d5db"
_BORDER_HI  = "#9ca3af"
_TEXT        = "#1f2937"
_TEXT_MUTED  = "#6b7280"
_TEXT_HINT   = "#9ca3af"
_ACCENT      = "#2563eb"
_ACCENT_HI   = "#1d4ed8"
_ACCENT_DOWN = "#3b82f6"
_DANGER      = "#dc2626"
_DANGER_HI   = "#b91c1c"
_GREEN       = "#16a34a"
_SLIDER_BG   = "#e5e7eb"

LIGHT_THEME = f"""

/* общие стили */
QWidget {{
    background-color: {_BG};
    color: {_TEXT};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {_BG};
}}

/* надписи */
QLabel {{
    color: {_TEXT};
    background: transparent;
    padding: 2px;
}}

QLabel#sectionTitle {{
    font-size: 13px;
    font-weight: 600;
    color: {_ACCENT};
    padding: 0;
    margin: 0;
}}

QLabel#statusIcon {{
    font-size: 22px;
    background: transparent;
}}

QLabel#progressLabel {{
    font-size: 12px;
    color: {_TEXT_MUTED};
}}

QLabel#hotkeyHint {{
    font-size: 11px;
    color: {_TEXT_HINT};
    padding: 4px 0;
}}

/* поле ввода кода */
QPlainTextEdit {{
    background-color: {_WHITE};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 10px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 13px;
    selection-background-color: #bfdbfe;
    selection-color: {_TEXT};
}}

QPlainTextEdit:focus {{
    border-color: {_ACCENT};
}}

/* кнопки */
QPushButton {{
    background-color: {_WHITE};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {_BG};
    border-color: {_BORDER_HI};
}}

QPushButton:pressed {{
    background-color: #e5e7eb;
}}

QPushButton:disabled {{
    background-color: {_BG};
    color: {_TEXT_HINT};
    border-color: #e5e7eb;
}}

QPushButton#primaryBtn {{
    background-color: {_ACCENT};
    color: white;
    border: none;
}}

QPushButton#primaryBtn:hover {{
    background-color: {_ACCENT_HI};
}}

QPushButton#primaryBtn:pressed {{
    background-color: {_ACCENT_DOWN};
}}

QPushButton#primaryBtn:disabled {{
    background-color: #93c5fd;
    color: white;
}}

QPushButton#dangerBtn {{
    background-color: {_DANGER};
    color: white;
    border: none;
}}

QPushButton#dangerBtn:hover {{
    background-color: {_DANGER_HI};
}}

QPushButton#dangerBtn:pressed {{
    background-color: #ef4444;
}}

/* прогресс-бар */
QProgressBar {{
    background-color: {_SLIDER_BG};
    border: none;
    border-radius: 4px;
    text-align: center;
    font-size: 11px;
    min-height: 8px;
    max-height: 8px;
}}

QProgressBar::chunk {{
    background-color: {_ACCENT};
    border-radius: 4px;
}}

/* ползунок задержки */
QSlider::groove:horizontal {{
    background: {_SLIDER_BG};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {_ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: {_ACCENT_HI};
}}

QSlider::sub-page:horizontal {{
    background: {_ACCENT};
    border-radius: 3px;
}}

/* скроллбары */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #d1d5db;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {_BORDER_HI};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: #d1d5db;
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {_BORDER_HI};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
    width: 0;
}}

/* подсказки */
QToolTip {{
    background-color: {_WHITE};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}}

/* карточка статуса */
QFrame#statusCard {{
    background-color: {_WHITE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 12px;
}}

QFrame#statusCard[active="true"] {{
    border-color: {_GREEN};
}}
"""
