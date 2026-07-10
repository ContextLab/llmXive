"""
Event catalog data model.

Represents a catalog of cosmic ray events with Energy, RA, Dec, and Source.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

@dataclass
class EventCatalog:
    """Container for a catalog of cosmic ray events."""
    energy: np.ndarray = field(default_factory=lambda: np.array([]))
    ra: np.ndarray = field(default_factory=lambda: np.array([]))
    dec: np.ndarray = field(default_factory=lambda: np.array([]))
    source: str = "unknown"
    n_events: int = 0

    def __post_init__(self):
        if self.n_events == 0:
            self.n_events = len(self.energy)

    def filter_by_energy(self, min_e: float) -> 'EventCatalog':
        """Return a new catalog filtered by minimum energy (EeV)."""
        mask = self.energy >= min_e
        return EventCatalog(
            energy=self.energy[mask],
            ra=self.ra[mask],
            dec=self.dec[mask],
            source=self.source,
            n_events=np.sum(mask)
        )

    def validate(self) -> bool:
        """Check for NaN coordinates or invalid energies."""
        if np.any(np.isnan(self.ra)) or np.any(np.isnan(self.dec)):
            return False
        if np.any(self.energy <= 0):
            return False
        return True
