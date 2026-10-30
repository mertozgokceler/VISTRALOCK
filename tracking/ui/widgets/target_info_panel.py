from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QGridLayout,
    QVBoxLayout
)

from PyQt5.QtCore import Qt


class TargetInfoPanel(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(
            220
        )

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            16,
            12,
            16,
            12
        )

        main_layout.setSpacing(
            8
        )

        title = QLabel(
            "TARGET INFORMATION"
        )

        title.setStyleSheet("""
            border: none;
            background: transparent;
            color: #CBD5E1;
            font-size: 15px;
            font-weight: 700;
            padding: 0px;
        """)

        main_layout.addWidget(
            title
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            20
        )

        grid.setVerticalSpacing(
            7
        )

        self.target_id_value = QLabel(
            "--"
        )

        self.distance_value = QLabel(
            "-- m"
        )

        self.bearing_value = QLabel(
            "--°"
        )

        self.heading_error_value = QLabel(
            "--°"
        )

        self.altitude_value = QLabel(
            "-- m"
        )

        self.direction_value = QLabel(
            "--"
        )

        self.suitability_value = QLabel(
            "-- %"
        )

        rows = [
            (
                "TARGET ID",
                self.target_id_value
            ),
            (
                "DISTANCE",
                self.distance_value
            ),
            (
                "BEARING",
                self.bearing_value
            ),
            (
                "HEADING ERROR",
                self.heading_error_value
            ),
            (
                "ALTITUDE DIFF",
                self.altitude_value
            ),
            (
                "DIRECTION",
                self.direction_value
            ),
            (
                "SUITABILITY",
                self.suitability_value
            )
        ]

        for row, (
            name,
            value_label
        ) in enumerate(rows):

            name_label = QLabel(
                name
            )

            name_label.setStyleSheet("""
                border: none;
                background: transparent;
                color: #94A3B8;
                font-size: 13px;
                font-weight: 700;
                padding: 1px;
            """)

            value_label.setAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            value_label.setStyleSheet("""
                border: none;
                background: transparent;
                color: #F8FAFC;
                font-size: 14px;
                font-weight: 700;
                padding: 1px;
            """)

            grid.addWidget(
                name_label,
                row,
                0
            )

            grid.addWidget(
                value_label,
                row,
                1
            )

        main_layout.addLayout(
            grid
        )

    def set_target_id(
        self,
        target_id
    ):

        self.target_id_value.setText(
            f"ID {target_id}"
        )

    def set_distance(
        self,
        distance
    ):

        self.distance_value.setText(
            f"{distance:.1f} m"
        )

    def set_bearing(
        self,
        bearing
    ):

        self.bearing_value.setText(
            f"{bearing:.1f}°"
        )

    def set_heading_error(
        self,
        error
    ):

        self.heading_error_value.setText(
            f"{error:+.1f}°"
        )

    def set_altitude_difference(
        self,
        difference
    ):

        self.altitude_value.setText(
            f"{difference:+.1f} m"
        )

    def set_direction(
        self,
        direction
    ):

        self.direction_value.setText(
            direction
        )

    def set_suitability(
        self,
        score
    ):

        self.suitability_value.setText(
            f"{score:.1f} %"
        )

    def update_metrics(
        self,
        metrics
    ):

        self.set_distance(
            metrics.distance
        )

        self.set_bearing(
            metrics.target_bearing
        )

        self.set_heading_error(
            metrics.heading_error
        )

        self.set_altitude_difference(
            metrics.altitude_difference
        )

        direction = (
            f"{metrics.horizontal_direction} / "
            f"{metrics.vertical_direction}"
        )

        self.set_direction(
            direction
        )

        self.set_suitability(
            metrics.suitability_score
        )

    def clear_data(
        self
    ):

        self.target_id_value.setText("--")
        self.distance_value.setText("-- m")
        self.bearing_value.setText("--°")
        self.heading_error_value.setText("--°")
        self.altitude_value.setText("-- m")
        self.direction_value.setText("--")
        self.suitability_value.setText("-- %")