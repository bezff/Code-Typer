"""Главное окно приложения Code Typer."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QLabel, QProgressBar,
    QSlider, QFrame, QSizePolicy, QSystemTrayIcon, QMenu, QAction,
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QFont

from ..core.engine import CodeTyperEngine


class _StatusCard(QFrame):
    """Карточка текущего состояния: работает / остановлен."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setProperty("active", False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # иконка статуса (юникод-эмодзи)
        self._icon = QLabel("⏸")
        self._icon.setObjectName("statusIcon")
        self._icon.setFixedWidth(28)
        self._icon.setAlignment(Qt.AlignCenter)

        info = QVBoxLayout()
        info.setSpacing(2)

        self._title = QLabel("Остановлен")
        self._title.setObjectName("sectionTitle")

        self._subtitle = QLabel("F6 — запуск / остановка")
        self._subtitle.setObjectName("hotkeyHint")

        info.addWidget(self._title)
        info.addWidget(self._subtitle)

        layout.addWidget(self._icon)
        layout.addLayout(info, 1)

    def set_active(self, active):
        """Обновить отображение карточки."""
        self._icon.setText("▶" if active else "⏸")
        self._title.setText("Печатает…" if active else "Остановлен")
        self.setProperty("active", active)
        # перерисовка стилей после смены свойства
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):
    """Главное окно — ввод кода, управление, прогресс."""

    _WINDOW_TITLE = "Code Typer"
    _MIN_SIZE = QSize(520, 620)

    def __init__(self, icon=None):
        super().__init__()
        self._engine = CodeTyperEngine()
        self._icon = icon or QIcon()

        self._init_window()
        self._build_ui()
        self._connect_signals()

    def _init_window(self):
        self.setWindowTitle(self._WINDOW_TITLE)
        self.setMinimumSize(self._MIN_SIZE)
        self.resize(560, 680)
        if not self._icon.isNull():
            self.setWindowIcon(self._icon)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # заголовок
        title = QLabel("Code Typer")
        title.setAlignment(Qt.AlignLeft)
        font = title.font()
        font.setPointSize(18)
        font.setWeight(QFont.Bold)
        title.setFont(font)
        root.addWidget(title)

        # карточка статуса
        self._status_card = _StatusCard()
        root.addWidget(self._status_card)

        # поле ввода кода
        code_label = QLabel("Код для воспроизведения")
        code_label.setObjectName("sectionTitle")
        root.addWidget(code_label)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setPlaceholderText(
            "Вставьте код сюда…\n\n"
            "Каждое нажатие клавиши будет воспроизводить\n"
            "следующий символ из этого текста."
        )
        self._code_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self._code_edit, 1)

        # секция прогресса
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)

        progress_title = QLabel("Прогресс")
        progress_title.setObjectName("sectionTitle")

        self._progress_label = QLabel("0 / 0")
        self._progress_label.setObjectName("progressLabel")
        self._progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        progress_row.addWidget(progress_title)
        progress_row.addWidget(self._progress_label)
        root.addLayout(progress_row)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        root.addWidget(self._progress_bar)

        # ползунок задержки
        delay_row = QHBoxLayout()
        delay_row.setSpacing(8)

        delay_title = QLabel("Задержка")
        delay_title.setObjectName("sectionTitle")

        self._delay_value_label = QLabel("0 мс")
        self._delay_value_label.setObjectName("progressLabel")
        self._delay_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._delay_value_label.setFixedWidth(60)

        delay_row.addWidget(delay_title)
        delay_row.addWidget(self._delay_value_label)
        root.addLayout(delay_row)

        self._delay_slider = QSlider(Qt.Horizontal)
        self._delay_slider.setRange(0, 200)
        self._delay_slider.setValue(0)
        self._delay_slider.setTickInterval(10)
        root.addWidget(self._delay_slider)

        # кнопки управления
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_load = QPushButton("Загрузить")
        self._btn_load.setObjectName("primaryBtn")
        self._btn_load.setToolTip("Загрузить код и начать слушать (F6 — старт)")

        self._btn_reset = QPushButton("Сброс")
        self._btn_reset.setToolTip("Вернуться к началу кода")

        self._btn_stop = QPushButton("Стоп")
        self._btn_stop.setObjectName("dangerBtn")
        self._btn_stop.setToolTip("Полностью остановить перехват клавиш")

        for btn in (self._btn_load, self._btn_reset, self._btn_stop):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_row.addWidget(btn)

        root.addLayout(btn_row)

        # подсказка по горячим клавишам
        hint = QLabel("F6 — переключить ввод  •  Вводите код в любом окне")
        hint.setObjectName("hotkeyHint")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

        self._update_btn_states(listening=False)

    # сигналы и слоты

    def _connect_signals(self):
        self._btn_load.clicked.connect(self._on_load)
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_stop.clicked.connect(self._on_stop)
        self._delay_slider.valueChanged.connect(self._on_delay_changed)

        self._engine.signals.progress_changed.connect(self._on_progress)
        self._engine.signals.toggled.connect(self._on_toggled)
        self._engine.signals.finished.connect(self._on_finished)

    @pyqtSlot()
    def _on_load(self):
        code = self._code_edit.toPlainText()
        if not code.strip():
            return
        self._engine.code = code
        self._engine.start_listener()
        self._update_btn_states(listening=True)

    @pyqtSlot()
    def _on_reset(self):
        self._engine.reset()

    @pyqtSlot()
    def _on_stop(self):
        self._engine.stop_listener()
        self._status_card.set_active(False)
        self._update_btn_states(listening=False)

    @pyqtSlot(int)
    def _on_delay_changed(self, value):
        self._engine.delay = value / 1000.0
        self._delay_value_label.setText(f"{value} мс")

    @pyqtSlot(int, int)
    def _on_progress(self, current, total):
        self._progress_label.setText(f"{current} / {total}")
        self._progress_bar.setRange(0, max(total, 1))
        self._progress_bar.setValue(current)

    @pyqtSlot(bool)
    def _on_toggled(self, active):
        self._status_card.set_active(active)

    @pyqtSlot()
    def _on_finished(self):
        self._status_card.set_active(False)

    def _update_btn_states(self, *, listening):
        self._btn_load.setEnabled(not listening)
        self._btn_reset.setEnabled(listening)
        self._btn_stop.setEnabled(listening)
        self._code_edit.setReadOnly(listening)

    def closeEvent(self, event):
        """При закрытии окна останавливаем хук."""
        self._engine.stop_listener()
        super().closeEvent(event)
