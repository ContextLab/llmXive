"""
Core data entities for the Cosmic Ray Anisotropy Solar-Cycle Modulation project.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np


@dataclass
class EventDataset:
    """
    Represents a collection of cosmic ray event data.
    
    Attributes:
        timestamps: List of datetime objects (UTC) representing event arrival times.
        ra: List of right ascension values in degrees.
        dec: List of declination values in degrees.
        energy: List of energy values (log10(E/eV)).
        detector_id: Identifier for the detector source (e.g., 'IceCube', 'Auger').
        metadata: Additional metadata dictionary.
    """
    timestamps: List[datetime] = field(default_factory=list)
    ra: List[float] = field(default_factory=list)
    dec: List[float] = field(default_factory=list)
    energy: List[float] = field(default_factory=list)
    detector_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.timestamps)

    def __bool__(self) -> bool:
        return len(self.timestamps) > 0

    @property
    def n_events(self) -> int:
        return len(self.timestamps)

    def to_arrays(self) -> Dict[str, np.ndarray]:
        """Convert lists to numpy arrays for efficient processing."""
        return {
            'timestamps': np.array(self.timestamps),
            'ra': np.array(self.ra),
            'dec': np.array(self.dec),
            'energy': np.array(self.energy)
        }


@dataclass
class SolarProxySeries:
    """
    Represents a time series of solar proxy indices (e.g., sunspot number, solar wind).
    
    Attributes:
        timestamps: List of datetime objects (UTC) for the proxy measurements.
        values: List of float values for the proxy index.
        proxy_type: String identifier for the proxy (e.g., 'sunspot', 'solar_wind').
        source: Data source identifier (e.g., 'NOAA', 'NGDC').
        metadata: Additional metadata dictionary.
    """
    timestamps: List[datetime] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    proxy_type: str = ""
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.timestamps)

    def __bool__(self) -> bool:
        return len(self.timestamps) > 0

    @property
    def n_points(self) -> int:
        return len(self.timestamps)

    def to_arrays(self) -> Dict[str, np.ndarray]:
        """Convert lists to numpy arrays for efficient processing."""
        return {
            'timestamps': np.array(self.timestamps),
            'values': np.array(self.values)
        }
