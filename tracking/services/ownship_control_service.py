import subprocess
import threading
import time

from pymavlink import mavutil

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot
)


class OwnshipControlService(QObject):

    throttle_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.ownship_aircraft_id = 2

        self.manual_aircraft_id = 2

        self.tmux_targets = {
            1: "talon:MAV1",
            2: "talon:MAV2",
            3: "talon:MAV3",
            4: "talon:MAV4",
            5: "talon:MAV5"
        }

        self.telemetry_connection = None

        self.running = True

        self.telemetry_thread = threading.Thread(
            target=self.telemetry_loop,
            daemon=True
        )

        self.telemetry_thread.start()

    @pyqtSlot(int)
    def set_aircraft(
        self,
        aircraft_id
    ):

        if aircraft_id not in self.tmux_targets:
            return

        self.manual_aircraft_id = aircraft_id

        print(
            f"MANUAL CONTROL AIRCRAFT -> ID {aircraft_id}"
        )

    @pyqtSlot(int, int)
    def send_manual_rc_command(
        self,
        channel,
        pwm
    ):

        if (
            self.manual_aircraft_id
            not in self.tmux_targets
        ):
            return

        tmux_target = (
            self.tmux_targets[
                self.manual_aircraft_id
            ]
        )

        self.send_rc_to_aircraft(
            tmux_target,
            self.manual_aircraft_id,
            channel,
            pwm
        )

    @pyqtSlot(int, int)
    def send_ownship_rc_command(
        self,
        channel,
        pwm
    ):

        tmux_target = (
            self.tmux_targets[
                self.ownship_aircraft_id
            ]
        )

        self.send_rc_to_aircraft(
            tmux_target,
            self.ownship_aircraft_id,
            channel,
            pwm
        )


    def send_target_rc_command(
        self,
        aircraft_id,
        channel,
        pwm
    ):

        if aircraft_id == self.ownship_aircraft_id:
            return

        tmux_target = self.tmux_targets.get(
            aircraft_id
        )

        if tmux_target is None:
            print(
                f"ID{aircraft_id}: RC bağlantısı tanımlı değil."
            )
            return

        self.send_rc_to_aircraft(
            tmux_target,
            aircraft_id,
            channel,
            pwm
        )

    def send_rc_to_aircraft(
        self,
        tmux_target,
        aircraft_id,
        channel,
        pwm
    ):

        if (
            channel < 1
            or channel > 8
        ):
            return

        pwm = int(
            max(
                1000,
                min(
                    2000,
                    pwm
                )
            )
        )

        command = (
            f"rc {channel} {pwm}"
        )

        try:

            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    tmux_target,
                    command,
                    "Enter"
                ],
                check=True
            )

            print(
                f"ID{aircraft_id} RC: "
                f"CH{channel} -> {pwm}"
            )

        except subprocess.CalledProcessError as error:

            print(
                f"ID{aircraft_id} RC command error:",
                error
            )

    def telemetry_loop(
        self
    ):

        while self.running:

            try:

                print(
                    "ID2 throttle telemetry bekleniyor..."
                )

                self.telemetry_connection = (
                    mavutil.mavlink_connection(
                        "udpin:127.0.0.1:14620",
                        source_system=255
                    )
                )

                heartbeat = (
                    self.telemetry_connection.wait_heartbeat(
                        timeout=10
                    )
                )

                if heartbeat is None:

                    print(
                        "ID2 telemetry heartbeat gelmedi."
                    )

                    self.close_telemetry()

                    time.sleep(2)

                    continue

                if heartbeat.get_srcSystem() != 2:

                    print(
                        "Yanlis SYSID geldi:",
                        heartbeat.get_srcSystem()
                    )

                    self.close_telemetry()

                    time.sleep(2)

                    continue

                print(
                    "ID2 throttle telemetry connected"
                )

                while self.running:

                    message = (
                        self.telemetry_connection.recv_match(
                            type="RC_CHANNELS",
                            blocking=True,
                            timeout=1
                        )
                    )

                    if message is None:
                        continue

                    if message.get_srcSystem() != 2:
                        continue

                    throttle_pwm = int(
                        message.chan3_raw
                    )

                    if (
                        900
                        <= throttle_pwm
                        <= 2100
                    ):

                        self.throttle_updated.emit(
                            throttle_pwm
                        )

            except Exception as error:

                if self.running:

                    print(
                        "ID2 telemetry error:",
                        error
                    )

                self.close_telemetry()

                if self.running:
                    time.sleep(2)

    def close_telemetry(
        self
    ):

        if self.telemetry_connection is not None:

            try:

                self.telemetry_connection.close()

            except Exception:

                pass

            self.telemetry_connection = None

    def stop(
        self
    ):

        self.running = False

        self.close_telemetry()