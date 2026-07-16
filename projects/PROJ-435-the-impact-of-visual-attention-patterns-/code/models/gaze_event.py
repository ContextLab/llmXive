"""Gaze event data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GazeEvent:
    """
    Represents a single gaze event (e.g., fixation or saccade).

    Attributes:
        timestamp: Timestamp of the event (ms or s).
        duration: Duration of the event (ms).
        roi: Region of Interest identifier (e.g., 'source_attribution').
        participant_id: ID of the participant who generated this event.
    """
    timestamp: float
    duration: float
    roi: str
    participant_id: str

    def __post_init__(self):
        """Validate numeric fields."""
        if not isinstance(self.timestamp, (int, float)):
            raise TypeError("timestamp must be numeric")
        if not isinstance(self.duration, (int, float)):
            raise TypeError("duration must be numeric")
        if not self.roi or not isinstance(self.roi, str):
            raise ValueError("roi must be a non-empty string")
        if not self.participant_id or not isinstance(self.participant_id, str):
            raise ValueError("participant_id must be a non-empty string")