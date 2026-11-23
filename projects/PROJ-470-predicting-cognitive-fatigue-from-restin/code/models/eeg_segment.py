from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np
import json

@dataclass
class EEGSegment:
    """
    Represents a validated segment of EEG data for a single participant.
    
    Attributes:
        participant_id: Unique identifier for the participant.
        channel: The EEG channel name (e.g., 'Fp1', 'Cz').
        data: The raw time-series data as a numpy array.
        sampling_rate: Sampling rate in Hz.
        start_time: Start timestamp of the segment.
        duration_seconds: Duration of the segment in seconds.
        metadata: Additional dictionary for segment-specific info.
    """
    participant_id: str
    channel: str
    data: np.ndarray
    sampling_rate: float
    start_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data types and basic constraints."""
        if not isinstance(self.data, np.ndarray):
            raise TypeError(f"data must be a numpy array, got {type(self.data)}")
        if self.data.ndim != 1:
            raise ValueError(f"data must be 1D, got {self.data.ndim}D")
        if self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be positive")
        
        # Calculate duration if not provided
        if self.duration_seconds is None and len(self.data) > 0:
            self.duration_seconds = len(self.data) / self.sampling_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert the segment to a dictionary for serialization."""
        return {
            'participant_id': self.participant_id,
            'channel': self.channel,
            'data': self.data.tolist(),
            'sampling_rate': self.sampling_rate,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'duration_seconds': self.duration_seconds,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EEGSegment':
        """Reconstruct an EEGSegment from a dictionary."""
        return cls(
            participant_id=data['participant_id'],
            channel=data['channel'],
            data=np.array(data['data']),
            sampling_rate=data['sampling_rate'],
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            duration_seconds=data.get('duration_seconds'),
            metadata=data.get('metadata', {})
        )

    def __len__(self) -> int:
        """Return the number of samples in the segment."""
        return len(self.data)
