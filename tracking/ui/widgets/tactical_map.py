#!/usr/bin/env python3

from PyQt5.QtWidgets import QWidget

from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPolygonF
)

from PyQt5.QtCore import (
    Qt,
    QPointF
)


class TacticalMap(QWidget):



    def __init__(self):

        super().__init__()

        self.setMinimumHeight(
            400
        )

        self.zoom = 1.0

        self.min_zoom = 0.3
        self.max_zoom = 5.0

        self.pan_x = 0.0
        self.pan_y = 0.0

        self.dragging = False

        self.last_mouse_position = None

        self.follow_own = True

        self.own_aircraft_id = 2

        self.aircraft_states = {}

        self.active_target_id = None

        self.heading_deg = 0.0




        self.setCursor(
            Qt.OpenHandCursor
        )

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#0B111A")
        )

        self.draw_grid(
            painter
        )


        self.draw_target_connection(
            painter
        )

        self.draw_all_aircraft(
            painter
        )

        self.draw_compass(
            painter
        )

        self.draw_follow_info(
            painter
        )

        self.draw_zoom_info(
            painter
        )

    def world_to_screen(
        self,
        world_x,
        world_y
    ):

        center_x = (
            self.width()
            / 2
        )

        center_y = (
            self.height()
            / 2
        )

        screen_x = (
            center_x
            + self.pan_x
            + world_x
            * self.zoom
        )

        screen_y = (
            center_y
            + self.pan_y
            - world_y
            * self.zoom
        )

        return QPointF(
            screen_x,
            screen_y
        )

    def screen_to_world(
        self,
        screen_x,
        screen_y
    ):

        center_x = (
            self.width()
            / 2
        )

        center_y = (
            self.height()
            / 2
        )

        world_x = (
            screen_x
            - center_x
            - self.pan_x
        ) / self.zoom

        world_y = (
            center_y
            + self.pan_y
            - screen_y
        ) / self.zoom

        return QPointF(
            world_x,
            world_y
        )

    def draw_grid(
        self,
        painter
    ):

        grid_size = 50.0

        top_left = (
            self.screen_to_world(
                0,
                0
            )
        )

        bottom_right = (
            self.screen_to_world(
                self.width(),
                self.height()
            )
        )

        min_x = min(
            top_left.x(),
            bottom_right.x()
        )

        max_x = max(
            top_left.x(),
            bottom_right.x()
        )

        min_y = min(
            top_left.y(),
            bottom_right.y()
        )

        max_y = max(
            top_left.y(),
            bottom_right.y()
        )

        grid_pen = QPen(
            QColor("#1E293B")
        )

        grid_pen.setWidth(
            1
        )

        painter.setPen(
            grid_pen
        )

        start_x = (
            int(
                min_x
                // grid_size
            )
            * grid_size
        )

        x = start_x

        while x <= max_x:

            p1 = (
                self.world_to_screen(
                    x,
                    min_y
                )
            )

            p2 = (
                self.world_to_screen(
                    x,
                    max_y
                )
            )

            painter.drawLine(
                p1,
                p2
            )

            x += grid_size

        start_y = (
            int(
                min_y
                // grid_size
            )
            * grid_size
        )

        y = start_y

        while y <= max_y:

            p1 = (
                self.world_to_screen(
                    min_x,
                    y
                )
            )

            p2 = (
                self.world_to_screen(
                    max_x,
                    y
                )
            )

            painter.drawLine(
                p1,
                p2
            )

            y += grid_size

    def draw_aircraft_connections(
        self,
        painter
    ):

        if (
            self.active_target_id
            is None
        ):
            return

        own_state = (
            self.aircraft_states.get(
                self.own_aircraft_id
            )
        )

        target_state = (
            self.aircraft_states.get(
                self.active_target_id
            )
        )

        if (
            own_state is None
            or target_state is None
        ):
            return

        own_position = (
            self.world_to_screen(
                own_state["x"],
                own_state["y"]
            )
        )

        target_position = (
            self.world_to_screen(
                target_state["x"],
                target_state["y"]
            )
        )

        pen = QPen(
            QColor("#475569")
        )

        pen.setWidth(
            2
        )

        pen.setStyle(
            Qt.DashLine
        )

        painter.setPen(
            pen
        )

        painter.drawLine(
            own_position,
            target_position
        )

    def draw_all_aircraft(
        self,
        painter
    ):

        for aircraft_id in sorted(
            self.aircraft_states.keys()
        ):

            state = (
                self.aircraft_states[
                    aircraft_id
                ]
            )

            screen_position = (
                self.world_to_screen(
                    state["x"],
                    state["y"]
                )
            )

            if (
                aircraft_id
                == self.own_aircraft_id
            ):

                color = QColor(
                    "#38BDF8"
                )

                label = (
                    f"ID {aircraft_id} • OWN"
                )

            elif (
                aircraft_id
                == self.active_target_id
            ):

                color = QColor(
                    "#FF1744"
                )

                label = (
                    f"ID {aircraft_id} • TARGET"
                )

            else:

                color = QColor(
                    "#FACC15"
                )

                label = (
                    f"ID {aircraft_id}"
                )

            self.draw_aircraft(
                painter,
                screen_position.x(),
                screen_position.y(),
                state["heading_deg"],
                color,
                label
            )

    def draw_target_connection(
        self,
        painter
    ):

        if (
            self.active_target_id
            is None
        ):
            return

        own_state = (
            self.aircraft_states.get(
                self.own_aircraft_id
            )
        )

        target_state = (
            self.aircraft_states.get(
                self.active_target_id
            )
        )

        if (
            own_state is None
            or target_state is None
        ):
            return

        own_position = (
            self.world_to_screen(
                own_state["x"],
                own_state["y"]
            )
        )

        target_position = (
            self.world_to_screen(
                target_state["x"],
                target_state["y"]
            )
        )

        self.draw_connection(
            painter,
            own_position,
            target_position
        )

    def draw_aircraft(
        self,
        painter,
        x,
        y,
        heading,
        color,
        label
    ):

        size = 12

        painter.save()

        painter.translate(
            x,
            y
        )

        painter.rotate(
            heading
        )

        aircraft = QPolygonF([
            QPointF(
                0,
                -size
            ),
            QPointF(
                -size,
                size
            ),
            QPointF(
                0,
                size / 2
            ),
            QPointF(
                size,
                size
            )
        ])

        painter.setPen(
            QPen(
                color,
                2
            )
        )

        painter.setBrush(
            QBrush(
                color
            )
        )

        painter.drawPolygon(
            aircraft
        )

        painter.restore()

        painter.setPen(
            color
        )

        painter.drawText(
            int(
                x + 18
            ),
            int(
                y + 5
            ),
            label
        )

    def draw_compass(
        self,
        painter
    ):

        center_x = 65
        center_y = 65

        radius = 38

        painter.setPen(
            QPen(
                QColor("#334155"),
                2
            )
        )

        painter.setBrush(
            QBrush(
                QColor("#101826")
            )
        )

        painter.drawEllipse(
            QPointF(
                center_x,
                center_y
            ),
            radius,
            radius
        )

        painter.setPen(
            QColor("#94A3B8")
        )

        painter.drawText(
            center_x - 5,
            center_y - 45,
            "N"
        )

        painter.drawText(
            center_x + 43,
            center_y + 5,
            "E"
        )

        painter.drawText(
            center_x - 5,
            center_y + 53,
            "S"
        )

        painter.drawText(
            center_x - 52,
            center_y + 5,
            "W"
        )

        own_state = (
            self.aircraft_states.get(
                self.own_aircraft_id
            )
        )

        heading = 0.0

        if own_state is not None:

            heading = (
                own_state[
                    "heading_deg"
                ]
            )

        painter.save()

        painter.translate(
            center_x,
            center_y
        )

        painter.rotate(
            heading
        )

        painter.setPen(
            QPen(
                QColor("#FF1744"),
                3
            )
        )

        painter.drawLine(
            0,
            8,
            0,
            -28
        )

        painter.setBrush(
            QColor("#FF1744")
        )

        pointer = QPolygonF([
            QPointF(
                0,
                -34
            ),
            QPointF(
                -6,
                -24
            ),
            QPointF(
                6,
                -24
            )
        ])

        painter.drawPolygon(
            pointer
        )

        painter.restore()

    def draw_follow_info(
        self,
        painter
    ):

        painter.setPen(
            QColor("#64748B")
        )

        if self.follow_own:

            text = "FOLLOW: OWN"

        else:

            text = "FOLLOW: FREE"

        painter.drawText(
            12,
            self.height() - 30,
            text
        )

    def draw_zoom_info(
        self,
        painter
    ):

        painter.setPen(
            QColor("#64748B")
        )

        text = (
            f"ZOOM: {self.zoom:.2f}x"
        )

        painter.drawText(
            12,
            self.height() - 12,
            text
        )


    def set_aircraft_states(
        self,
        aircraft_states
    ):

        self.aircraft_states = (
            aircraft_states.copy()
        )

        own_state = (
            self.aircraft_states.get(
                self.own_aircraft_id
            )
        )

        if own_state is not None:

            self.heading_deg = (
                own_state[
                    "heading_deg"
                ]
            )

            self.own_x = (
                own_state[
                    "x"
                ]
            )

            self.own_y = (
                own_state[
                    "y"
                ]
            )

            if self.follow_own:

                self.center_on_own()

                return

        self.update()


    def set_active_target_id(
        self,
        aircraft_id
    ):

        self.active_target_id = (
            aircraft_id
        )

        self.update()


    def set_own_aircraft_id(
        self,
        aircraft_id
    ):

        self.own_aircraft_id = int(
            aircraft_id
        )

        self.update()

    def center_on_own(
        self
    ):

        own_state = (
            self.aircraft_states.get(
                self.own_aircraft_id
            )
        )

        if own_state is None:
            return

        self.pan_x = (
            -own_state["x"]
            * self.zoom
        )

        self.pan_y = (
            own_state["y"]
            * self.zoom
        )

        self.update()

    def wheelEvent(
        self,
        event
    ):

        if (
            event.angleDelta().y()
            > 0
        ):

            new_zoom = (
                self.zoom
                * 1.15
            )

        else:

            new_zoom = (
                self.zoom
                / 1.15
            )

        self.zoom = max(
            self.min_zoom,
            min(
                new_zoom,
                self.max_zoom
            )
        )

        if self.follow_own:

            self.center_on_own()

        else:

            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        self.dragging = True
        self.last_mouse_position = event.pos()
        self.setCursor(Qt.ClosedHandCursor)


    def mouseMoveEvent(self, event):
        if not self.dragging or self.last_mouse_position is None:
            return

        delta = event.pos() - self.last_mouse_position
        self.follow_own = False
        self.pan_x += delta.x()
        self.pan_y += delta.y()
        self.last_mouse_position = event.pos()
        self.update()


    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        self.dragging = False
        self.last_mouse_position = None
        self.setCursor(Qt.OpenHandCursor)


    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.follow_own = True
            self.center_on_own()




    def clear_aircraft(
        self
    ):

        self.aircraft_states = {}

        self.active_target_id = None

        self.heading_deg = 0.0

        self.pan_x = 0.0
        self.pan_y = 0.0

        self.update()