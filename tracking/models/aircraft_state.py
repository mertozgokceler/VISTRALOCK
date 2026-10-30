from dataclasses import dataclass


@dataclass
class AircraftState:

    aircraft_id: int
    model_name: str

    x: float
    y: float
    z: float

    roll_deg: float
    pitch_deg: float
    yaw_deg: float

    compass_heading_deg: float

    velocity_x: float
    velocity_y: float
    velocity_z: float