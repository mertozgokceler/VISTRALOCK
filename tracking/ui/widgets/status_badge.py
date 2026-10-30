from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt


class StatusBadge(QLabel):

    def __init__(self):
        super().__init__()

        self.current_status = "SEARCH"

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setFixedSize(
            200,
            34
        )

        self.update_style()

    def set_status(
        self,
        status
    ):
        self.current_status = status.upper()

        self.update_style()

    def update_style(self):

        colors = {
            "SEARCH": (
                "#0E2A3A",
                "#38BDF8",
                "#0EA5E9"
            ),

            "CANDIDATE": (
                "#332A0A",
                "#FACC15",
                "#EAB308"
            ),

            "ACQUIRE": (
                "#351A0A",
                "#FB923C",
                "#F97316"
            ),

            "VISUAL TRACKING": (
                "#0D2B1A",
                "#4ADE80",
                "#22C55E"
            ),

            "REACQUIRE": (
                "#261442",
                "#C084FC",
                "#A855F7"
            ),

            "LOST": (
                "#3A1010",
                "#F87171",
                "#EF4444"
            ),

            "STANDBY": (
                "#1E293B",
                "#94A3B8",
                "#475569"
            )
        }

        background, text, border = colors.get(
            self.current_status,
            colors["SEARCH"]
        )

        self.setText(
            f"STATUS: {self.current_status}"
        )

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }}
        """)