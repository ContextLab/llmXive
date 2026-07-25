"""
GazeEvent data model.

Represents a single gaze event (fixation or saccade) with its
timestamp, duration, region of interest (ROI), and associated participant.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class GazeEvent:
    """
    Represents a gaze event from eye-tracking data.
    
    Attributes:
        timestamp: Timestamp of the event (in milliseconds or seconds).
        duration: Duration of the event (in milliseconds).
        roi: Region of Interest identifier (e.g., 'source', 'headline', 'control').
        participant_id: ID of the participant who generated this event.
    """
    timestamp: float
    duration: float
    roi: str
    participant_id: str

    def __post_init__(self):
        """Ensure numeric fields are floats."""
        if not isinstance(self.timestamp, (int, float)):
            try:
                self.timestamp = float(self.timestamp)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid timestamp: {self.timestamp}")
        
        if not isinstance(self.duration, (int, float)):
            try:
                self.duration = float(self.duration)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid duration: {self.duration}")