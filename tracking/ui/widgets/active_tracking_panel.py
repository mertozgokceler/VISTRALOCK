from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QHBoxLayout
)

from PyQt5.QtCore import pyqtSignal


class ActiveTrackingPanel(QFrame):

    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setFixedHeight(
            58
        )

        self.setStyleSheet("""
            ActiveTrackingPanel {
                background-color: #0D2318;
                border: 1px solid #22C55E;
                border-radius: 9px;
            }
        """)

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            8,
            14,
            8
        )

        layout.setSpacing(
            12
        )

        self.status_label = QLabel(
            "●  ID 1 TAKIP EDILIYOR"
        )

        self.status_label.setStyleSheet("""
            border: none;
            background: transparent;
            color: #4ADE80;
            font-size: 13px;
            font-weight: bold;
            padding: 0px;
        """)

        self.stop_button = QPushButton(
            "STOP TRACKING"
        )

        self.stop_button.setFixedHeight(
            32
        )

        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #3A1010;
                color: #F87171;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 0px 14px;
                font-size: 11px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #511616;
            }

            QPushButton:pressed {
                background-color: #6B1C1C;
            }
        """)

        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

        layout.addWidget(
            self.stop_button
        )

        self.hide()

    def start_tracking(
        self,
        target_id=1
    ):

        self.status_label.setText(
            f"●  ID {target_id} FOLLOWING"
        )

        self.show()

    def stop_tracking(
        self
    ):

        self.hide()