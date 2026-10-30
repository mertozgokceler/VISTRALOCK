from PyQt5.QtWidgets import (
    QLabel,
    QGraphicsDropShadowEffect
)

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor


class OnlineIndicator(QLabel):

    def __init__(self):
        super().__init__()

        self.online = False
        self.is_on = False

        self.setFixedSize(
            12,
            12
        )

        self.glow = QGraphicsDropShadowEffect(
            self
        )

        self.glow.setBlurRadius(
            18
        )

        self.glow.setOffset(
            0,
            0
        )

        self.setGraphicsEffect(
            self.glow
        )

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.blink
        )

        self.update_style()

    def blink(self):

        if not self.online:
            return

        self.is_on = not self.is_on

        self.update_style()

    def set_online(
        self,
        online
    ):

        self.online = online

        if self.online:

            self.is_on = True

            if not self.timer.isActive():
                self.timer.start(
                    600
                )

        else:

            self.timer.stop()

        self.update_style()

    def update_style(self):

        if not self.online:

            color = "#FF1744"

        elif self.is_on:

            color = "#39FF14"

        else:

            color = "#13551B"

        self.glow.setColor(
            QColor(color)
        )

        self.setStyleSheet(f"""
            background-color: {color};
            border: none;
            border-radius: 6px;
            padding: 0px;
        """)