"""
Gaze Event data model.
Represents a single fixation or gaze event recorded during the study.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GazeEvent:
    """
    Represents a single gaze event (fixation).

    Attributes:
        timestamp: Timestamp of the event (relative to trial start or absolute).
        duration: Duration of the fixation in milliseconds.
        roi: Region of Interest identifier (e.g., 'source_attribution', 'headline').
        participant_id: ID of the participant who generated this event.
    """
    timestamp: float
    duration: float
    roi: str
    participant_id: str

    def __post_init__(self):
        """Ensure numeric fields are floats."""
        self.timestamp = float(self.timestamp)
        self.duration = float(self.duration)
