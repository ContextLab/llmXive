"""
Gaze Event data model.

Represents a single gaze event (e.g., fixation or saccade) extracted from
eye-tracking data during the visual attention experiment.
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

    def __post_init__(self):
        """Validate GazeEvent fields after initialization."""
        if not isinstance(self.timestamp, (int, float)):
            raise TypeError(f"timestamp must be numeric, got {type(self.timestamp)}")
        if not isinstance(self.duration, (int, float)):
            raise TypeError(f"duration must be numeric, got {type(self.duration)}")
        if self.duration < 0:
            raise ValueError(f"duration must be non-negative, got {self.duration}")
        if not isinstance(self.roi, str):
            raise TypeError(f"roi must be a string, got {type(self.roi)}")
        if not self.roi.strip():
            raise ValueError("roi cannot be an empty string")
        if not isinstance(self.participant_id, str):
            raise TypeError(f"participant_id must be a string, got {type(self.participant_id)}")
        if not self.participant_id.strip():
            raise ValueError("participant_id cannot be an empty string")

    def to_dict(self) -> dict:
        """Convert the GazeEvent to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "duration": self.duration,
            "roi": self.roi,
            "participant_id": self.participant_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GazeEvent":
        """Create a GazeEvent instance from a dictionary."""
        required_fields = ["timestamp", "duration", "roi", "participant_id"]
        for field in required_fields:
            if field not in data:
                raise KeyError(f"Missing required field '{field}' in GazeEvent data")
        return cls(
            timestamp=data["timestamp"],
            duration=data["duration"],
            roi=data["roi"],
            participant_id=data["participant_id"]
        )