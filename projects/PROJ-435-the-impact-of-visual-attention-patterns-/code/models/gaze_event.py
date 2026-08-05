"""Gaze event data model."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class GazeEvent:
    """
    Represents a single gaze event (fixation or saccade).

    Attributes:
        timestamp: Timestamp of the event in milliseconds.
        duration: Duration of the event in milliseconds.
        roi: Region of Interest identifier (e.g., 'source_attribution').
        participant_id: ID of the participant who generated this event.
    """
    timestamp: float
    duration: float
    roi: str
    participant_id: str
