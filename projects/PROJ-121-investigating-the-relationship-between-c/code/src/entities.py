"""
Data entity definitions for the cosmic ray anisotropy analysis pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np


@dataclass
class EventDataset:
    """
    Container for cosmic ray event data.

    Attributes:
        events: List of event dictionaries, each containing at least:
            - timestamp: datetime or ISO string
            - ra: Right Ascension (degrees)
            - dec: Declination (degrees)
            - energy: Energy (optional, in GeV or TeV)
            - detector_id: Optional detector identifier
        detector_name: Name of the detector (e.g., 'IceCube', 'Auger')
        metadata: Additional metadata dictionary
    """
    events: List[Dict[str, Any]] = field(default_factory=list)
    detector_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize events after initialization."""
        if self.events is None:
            self.events = []

        # Ensure all events have required fields
        for i, event in enumerate(self.events):
            if 'timestamp' not in event:
                raise ValueError(f"Event {i} missing 'timestamp' field")
            if 'ra' not in event:
                raise ValueError(f"Event {i} missing 'ra' field")
            if 'dec' not in event:
                raise ValueError(f"Event {i} missing 'dec' field")

    def __len__(self) -> int:
        return len(self.events)

    def __bool__(self) -> bool:
        return len(self.events) > 0


@dataclass
class SolarProxySeries:
    """
    Container for solar proxy time series data.

    Attributes:
        timestamps: List of datetime objects (UTC)
        values: List of float values corresponding to timestamps
        proxy_name: Name of the solar proxy (e.g., 'sunspot_number', 'solar_wind_speed')
        source: Data source (e.g., 'NOAA', 'NGDC')
        metadata: Additional metadata dictionary
    """
    timestamps: List[datetime] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    proxy_name: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.timestamps is None:
            self.timestamps = []
        if self.values is None:
            self.values = []

        if len(self.timestamps) != len(self.values):
            raise ValueError(
                f"timestamps ({len(self.timestamps)}) and values "
                f"({len(self.values)}) must have the same length"
            )

    def __len__(self) -> int:
        return len(self.timestamps)

    def __bool__(self) -> bool:
        return len(self.timestamps) > 0

    def get_array(self) -> np.ndarray:
        """Return values as a numpy array."""
        return np.array(self.values)

    def get_timestamps_array(self) -> np.ndarray:
        """Return timestamps as a numpy array of Julian dates."""
        from .utils import julian_date
        return np.array([julian_date(ts) for ts in self.timestamps])