from dataclasses import dataclass


@dataclass
class TrackingMetrics:

    distance: float
    altitude_difference: float

    target_bearing: float
    heading_error: float

    horizontal_direction: str
    vertical_direction: str

    suitability_score: float
    candidate_ok: bool