from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QComboBox
)

from PyQt5.QtCore import (
    Qt,
    pyqtSignal
)


class OwnshipControlPanel(QFrame):

    rc_command = pyqtSignal(
        int,
        int
    )

    aircraft_changed = pyqtSignal(
        int
    )

    def __init__(self):

        super().__init__()

        self.setFixedHeight(
            205
        )

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            10,
            7,
            10,
            7
        )

        main_layout.setSpacing(
            5
        )

        title = QLabel(
            "AIRCRAFT CONTROL"
        )

        title.setStyleSheet("""
            border: none;
            background: transparent;
            color: #38BDF8;
            font-size: 12px;
            font-weight: bold;
            padding: 0px;
        """)

        main_layout.addWidget(
            title
        )

        aircraft_layout = QHBoxLayout()

        aircraft_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        aircraft_layout.setSpacing(
            8
        )

        aircraft_label = QLabel(
            "CONTROL AIRCRAFT"
        )

        aircraft_label.setStyleSheet("""
            border: none;
            background: transparent;
            color: #94A3B8;
            font-size: 11px;
            font-weight: bold;
            padding: 0px;
        """)

        self.aircraft_selector = QComboBox()

        self.aircraft_selector.setFixedWidth(
            130
        )

        self.aircraft_selector.setFixedHeight(
            28
        )

        self.aircraft_selector.setStyleSheet("""
            QComboBox {
                background-color: #101827;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
            }

            QComboBox:hover {
                border: 1px solid #0EA5E9;
            }

            QComboBox::drop-down {
                border: none;
                width: 22px;
            }

            QComboBox QAbstractItemView {
                background-color: #111827;
                color: #E8EDF5;
                border: 1px solid #334155;
                selection-background-color: #0E2A3A;
                selection-color: #38BDF8;
            }
        """)

        self.aircraft_selector.currentIndexChanged.connect(
            self.aircraft_selection_changed
        )

        aircraft_layout.addWidget(
            aircraft_label
        )

        aircraft_layout.addStretch()

        aircraft_layout.addWidget(
            self.aircraft_selector
        )

        main_layout.addLayout(
            aircraft_layout
        )

        control_grid = QGridLayout()

        control_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        control_grid.setHorizontalSpacing(
            6
        )

        control_grid.setVerticalSpacing(
            4
        )

        self.add_axis_control(
            control_grid,
            row=0,
            title="ROLL",
            channel=1,
            negative_text="LEFT",
            positive_text="RIGHT",
            negative_pwm=1350,
            positive_pwm=1650
        )

        self.add_axis_control(
            control_grid,
            row=1,
            title="PITCH",
            channel=4,
            negative_text="DOWN",
            positive_text="UP",
            negative_pwm=1900,
            positive_pwm=1100
        )

        self.add_axis_control(
            control_grid,
            row=2,
            title="RUDDER",
            channel=2,
            negative_text="LEFT",
            positive_text="RIGHT",
            negative_pwm=1100,
            positive_pwm=1900
        )

        main_layout.addLayout(
            control_grid
        )

        throttle_layout = QHBoxLayout()

        throttle_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        throttle_layout.setSpacing(
            6
        )

        throttle_label = QLabel(
            "THROTTLE"
        )

        throttle_label.setFixedWidth(
            62
        )

        throttle_label.setStyleSheet("""
            border: none;
            background: transparent;
            font-size: 11px;
            font-weight: bold;
            padding: 0px;
        """)

        self.throttle_slider = QSlider(
            Qt.Horizontal
        )

        self.throttle_slider.setRange(
            1000,
            2000
        )

        self.throttle_slider.setSingleStep(
            10
        )

        self.throttle_slider.setPageStep(
            50
        )

        self.throttle_slider.setValue(
            1500
        )

        self.throttle_value = QLabel(
            "50%"
        )

        self.throttle_value.setFixedWidth(
            46
        )

        self.throttle_value.setAlignment(
            Qt.AlignCenter
        )

        self.throttle_value.setStyleSheet("""
            background-color: #101827;
            border: 1px solid #334155;
            border-radius: 5px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px;
        """)

        self.throttle_slider.valueChanged.connect(
            self.throttle_changed
        )

        throttle_layout.addWidget(
            throttle_label
        )

        throttle_layout.addWidget(
            self.throttle_slider,
            1
        )

        throttle_layout.addWidget(
            self.throttle_value
        )

        main_layout.addLayout(
            throttle_layout
        )

        self.neutral_button = QPushButton(
            "NEUTRALIZE"
        )

        self.neutral_button.setFixedHeight(
            26
        )

        self.neutral_button.setStyleSheet("""
            QPushButton {
                background-color: #172033;
                color: #CBD5E1;
                border: 1px solid #475569;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
            }

            QPushButton:pressed {
                background-color: #263449;
            }
        """)

        self.neutral_button.clicked.connect(
            self.neutralize
        )

        main_layout.addWidget(
            self.neutral_button
        )

    def set_aircraft_ids(
        self,
        aircraft_ids
    ):

        aircraft_ids = sorted(
            set(
                int(aircraft_id)
                for aircraft_id
                in aircraft_ids
            )
        )

        current_id = (
            self.aircraft_selector.currentData()
        )

        self.aircraft_selector.blockSignals(
            True
        )

        self.aircraft_selector.clear()

        for aircraft_id in aircraft_ids:

            if aircraft_id == 2:

                text = (
                    f"ID {aircraft_id} • OWN"
                )

            else:

                text = (
                    f"ID {aircraft_id}"
                )

            self.aircraft_selector.addItem(
                text,
                aircraft_id
            )

        selected_index = -1

        if current_id is not None:

            selected_index = (
                self.aircraft_selector.findData(
                    current_id
                )
            )

        if selected_index < 0:

            selected_index = (
                self.aircraft_selector.findData(
                    2
                )
            )

        if (
            selected_index < 0
            and
            self.aircraft_selector.count() > 0
        ):

            selected_index = 0

        if selected_index >= 0:

            self.aircraft_selector.setCurrentIndex(
                selected_index
            )

        self.aircraft_selector.blockSignals(
            False
        )

        if selected_index >= 0:

            selected_aircraft_id = (
                self.aircraft_selector.itemData(
                    selected_index
                )
            )

            if selected_aircraft_id is not None:

                self.aircraft_changed.emit(
                    int(
                        selected_aircraft_id
                    )
                )

    def aircraft_selection_changed(
        self,
        index
    ):

        if index < 0:
            return

        aircraft_id = (
            self.aircraft_selector.itemData(
                index
            )
        )

        if aircraft_id is None:
            return

        self.aircraft_changed.emit(
            int(
                aircraft_id
            )
        )

    def add_axis_control(
        self,
        layout,
        row,
        title,
        channel,
        negative_text,
        positive_text,
        negative_pwm,
        positive_pwm
    ):

        title_label = QLabel(
            title
        )

        title_label.setFixedWidth(
            62
        )

        title_label.setStyleSheet("""
            border: none;
            background: transparent;
            font-size: 11px;
            font-weight: bold;
            padding: 0px;
        """)

        negative_button = QPushButton(
            negative_text
        )

        center_button = QPushButton(
            "CENTER"
        )

        positive_button = QPushButton(
            positive_text
        )

        buttons = [
            negative_button,
            center_button,
            positive_button
        ]

        for button in buttons:

            button.setFixedHeight(
                24
            )

            button.setStyleSheet("""
                QPushButton {
                    background-color: #101827;
                    color: #CBD5E1;
                    border: 1px solid #334155;
                    border-radius: 5px;
                    font-size: 10px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    border: 1px solid #38BDF8;
                    color: #38BDF8;
                }

                QPushButton:pressed {
                    background-color: #0E2A3A;
                    color: #FFFFFF;
                }
            """)

        negative_button.pressed.connect(
            lambda ch=channel, pwm=negative_pwm:
            self.rc_command.emit(
                ch,
                pwm
            )
        )

        negative_button.released.connect(
            lambda ch=channel:
            self.rc_command.emit(
                ch,
                1500
            )
        )

        positive_button.pressed.connect(
            lambda ch=channel, pwm=positive_pwm:
            self.rc_command.emit(
                ch,
                pwm
            )
        )

        positive_button.released.connect(
            lambda ch=channel:
            self.rc_command.emit(
                ch,
                1500
            )
        )

        center_button.clicked.connect(
            lambda checked=False, ch=channel:
            self.rc_command.emit(
                ch,
                1500
            )
        )

        layout.addWidget(
            title_label,
            row,
            0
        )

        layout.addWidget(
            negative_button,
            row,
            1
        )

        layout.addWidget(
            center_button,
            row,
            2
        )

        layout.addWidget(
            positive_button,
            row,
            3
        )

    def throttle_changed(
        self,
        pwm
    ):

        self.update_throttle_display(
            pwm
        )

        self.rc_command.emit(
            3,
            pwm
        )

    def set_throttle_from_aircraft(
        self,
        pwm
    ):

        pwm = max(
            1000,
            min(
                2000,
                int(
                    pwm
                )
            )
        )

        if self.throttle_slider.isSliderDown():
            return

        self.throttle_slider.blockSignals(
            True
        )

        self.throttle_slider.setValue(
            pwm
        )

        self.throttle_slider.blockSignals(
            False
        )

        self.update_throttle_display(
            pwm
        )

    def update_throttle_display(
        self,
        pwm
    ):

        percentage = int(
            (
                pwm - 1000
            )
            / 10
        )

        percentage = max(
            0,
            min(
                100,
                percentage
            )
        )

        self.throttle_value.setText(
            f"{percentage}%"
        )

    def neutralize(
        self
    ):

        self.rc_command.emit(
            1,
            1500
        )

        self.rc_command.emit(
            2,
            1500
        )

        self.rc_command.emit(
            4,
            1500
        )