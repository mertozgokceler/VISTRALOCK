from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout
)

from PyQt5.QtCore import (
    pyqtSignal,
    Qt
)


class CandidatePanel(QFrame):

    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setFixedHeight(
            190
        )

        self.setStyleSheet("""
            CandidatePanel {
                background-color: #151A23;
                border: 1px solid #EAB308;
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        main_layout.setSpacing(
            9
        )

        self.title_label = QLabel(
            "TARGET CANDIDATE"
        )

        self.title_label.setStyleSheet("""
            border: none;
            background: transparent;
            color: #FACC15;
            font-size: 13px;
            font-weight: bold;
            padding: 0px;
        """)

        self.info_label = QLabel(
            "ID 1 may suitable for tracking."
        )

        self.info_label.setStyleSheet("""
            border: none;
            background: transparent;
            color: #E8EDF5;
            font-size: 12px;
            padding: 0px;
        """)

        metrics_layout = QHBoxLayout()

        metrics_layout.setSpacing(
            8
        )

        self.distance_box = self.create_metric_box(
            "MESAFE",
            "-- m"
        )

        self.suitability_box = self.create_metric_box(
            "UYGUNLUK",
            "-- %"
        )

        self.direction_box = self.create_metric_box(
            "YON",
            "--"
        )

        metrics_layout.addWidget(
            self.distance_box
        )

        metrics_layout.addWidget(
            self.suitability_box
        )

        metrics_layout.addWidget(
            self.direction_box
        )

        button_layout = QHBoxLayout()

        button_layout.setSpacing(
            10
        )

        self.accept_button = QPushButton(
            "START TRACKING"
        )

        self.reject_button = QPushButton(
            "CANCEL"
        )

        self.accept_button.setFixedHeight(
            36
        )

        self.reject_button.setFixedHeight(
            36
        )

        self.accept_button.setStyleSheet("""
            QPushButton {
                background-color: #0D2B1A;
                color: #4ADE80;
                border: 1px solid #22C55E;
                border-radius: 7px;
                padding: 0px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #123D25;
            }

            QPushButton:pressed {
                background-color: #18542F;
            }
        """)

        self.reject_button.setStyleSheet("""
            QPushButton {
                background-color: #3A1010;
                color: #F87171;
                border: 1px solid #EF4444;
                border-radius: 7px;
                padding: 0px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #511616;
            }

            QPushButton:pressed {
                background-color: #6B1C1C;
            }
        """)

        self.accept_button.clicked.connect(
            self.accepted.emit
        )

        self.reject_button.clicked.connect(
            self.rejected.emit
        )

        button_layout.addWidget(
            self.accept_button
        )

        button_layout.addWidget(
            self.reject_button
        )

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addWidget(
            self.info_label
        )

        main_layout.addLayout(
            metrics_layout
        )

        main_layout.addLayout(
            button_layout
        )

        self.hide()

    def create_metric_box(
        self,
        title,
        value
    ):

        box = QLabel()

        box.setAlignment(
            Qt.AlignCenter
        )

        box.setMinimumHeight(
            45
        )

        box.setText(
            f"{title}\n{value}"
        )

        box.setStyleSheet("""
            QLabel {
                background-color: #0F1722;
                color: #E8EDF5;
                border: 1px solid #263244;
                border-radius: 7px;
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
            }
        """)

        return box

    def show_candidate(
        self,
        metrics
    ):

        self.distance_box.setText(
            "DISTANCE\n"
            f"{metrics.distance:.1f} m"
        )

        self.suitability_box.setText(
            "SUITIBILITY\n"
            f"{metrics.suitability_score:.1f} %"
        )

        self.direction_box.setText(
            "DIRECTION\n"
            f"{metrics.horizontal_direction}"
        )

        self.show()

    def clear_candidate(
        self
    ):

        self.hide()