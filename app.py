"""Точка входа — запуск приложения Code Typer."""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.ui.theme import LIGHT_THEME
from src.icon_gen import ensure_icon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Code Typer")
    app.setOrganizationName("CodeTyper")
    app.setStyleSheet(LIGHT_THEME)

    # создаём иконку при первом запуске и ставим её
    icon_path = ensure_icon()
    icon = QIcon(str(icon_path))
    app.setWindowIcon(icon)

    window = MainWindow(icon=icon)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
