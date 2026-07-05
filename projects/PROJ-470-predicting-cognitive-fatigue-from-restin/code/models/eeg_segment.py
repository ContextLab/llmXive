"""
Data model for a single EEG segment (epoch).
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import numpy as np


@dataclass
class EEGSegment:
    """
    Represents a continuous or epoched segment of EEG data.
    
    Attributes:
        participant_id: Unique identifier for the participant.
        segment_id: Unique identifier for this specific segment/epoch.
        recording_date: Date and time of the recording.
        channel_names: List of channel names included in this segment.
        sampling_rate: Sampling rate in Hz.
        data: 2D numpy array of shape (n_channels, n_samples).
        metadata: Additional metadata dictionary (e.g., sleep stage, task condition).
        is_resting: Boolean flag indicating if this segment is a resting-state recording.
        duration_seconds: Duration of the segment in seconds.
        rejection_reason: Optional string explaining why this segment was rejected (if applicable).
    """
    participant_id: str
    segment_id: str
    sampling_rate: float
    channel_names: list[str]
    data: np.ndarray
    
    recording_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_resting: bool = False
    duration_seconds: Optional[float] = None
    rejection_reason: Optional[str] = None

    def __post_init__(self):
        """Validate data shape and types after initialization."""
        if not isinstance(self.channel_names, list):
            raise TypeError("channel_names must be a list of strings.")
        
        if not isinstance(self.data, np.ndarray):
            raise TypeError("data must be a numpy ndarray.")
        
        if self.data.ndim != 2:
            raise ValueError(f"Expected 2D data array (channels, samples), got {self.data.ndim}D.")
        
        expected_channels = len(self.channel_names)
        if self.data.shape[0] != expected_channels:
            raise ValueError(
                f"Channel count mismatch: {expected_channels} channel names provided, "
                f"but data array has {self.data.shape[0]} rows."
            )
        
        if self.duration_seconds is None and self.sampling_rate > 0:
            self.duration_seconds = self.data.shape[1] / self.sampling_rate

    def get_channel_data(self, channel_name: str) -> np.ndarray:
        """
        Retrieve data for a specific channel by name.
        
        Args:
            channel_name: The name of the channel.
            
        Returns:
            1D numpy array of channel data.
            
        Raises:
            ValueError: If the channel name is not found.
        """
        if channel_name not in self.channel_names:
            raise ValueError(f"Channel '{channel_name}' not found in segment.")
        
        idx = self.channel_names.index(channel_name)
        return self.data[idx, :]
