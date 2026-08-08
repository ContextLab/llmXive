"""
Gaze Event data model.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GazeEvent:
    """
    Represents a single gaze event (e.g., fixation or saccade).

    Attributes:
        timestamp: Timestamp of the event (ms or seconds relative to trial start).
        duration: Duration of the event (ms).
        roi: Region of Interest name (e.g., "source_attribution", "headline_body").
        participant_id: ID of the participant who generated this event.
    """
    timestamp: float
    duration: float
    roi: str
    participant_id: str
