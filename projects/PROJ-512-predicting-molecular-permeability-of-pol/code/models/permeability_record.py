"""
Data model for permeability measurements associated with polymer structures.

This module defines the `PermeabilityRecord` dataclass, which encapsulates
the target variable (permeability) and its metadata for a specific polymer.
It is designed to be used in conjunction with the `PolymerGraph` entity.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class PermeabilityRecord:
    """
    Represents a single permeability measurement record for a polymer.

    Attributes:
        polymer_id: Unique identifier for the polymer (matches PolymerGraph.id).
        log_permeability: The natural logarithm of the permeability coefficient
            (typically in units of Barrer or similar, depending on source).
        source: The database or publication from which this measurement was obtained
            (e.g., 'NIST', 'PubChem', 'Literature').
        temperature: Temperature in Kelvin at which the measurement was taken.
        pressure: Pressure in atm at which the measurement was taken.
        gas_species: The gas species used for permeability measurement (e.g., 'O2', 'N2').
        metadata: Additional free-form attributes stored as a dictionary.
    """
    polymer_id: str
    log_permeability: float
    source: str = "Unknown"
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    gas_species: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not isinstance(self.polymer_id, str) or not self.polymer_id:
            raise ValueError("polymer_id must be a non-empty string.")

        if not isinstance(self.log_permeability, (int, float)):
            raise TypeError("log_permeability must be a numeric value.")

        # Ensure float for numerical stability
        self.log_permeability = float(self.log_permeability)

        # Initialize metadata if None
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "polymer_id": self.polymer_id,
            "log_permeability": self.log_permeability,
            "source": self.source,
            "temperature": self.temperature,
            "pressure": self.pressure,
            "gas_species": self.gas_species,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermeabilityRecord":
        """Create a PermeabilityRecord instance from a dictionary."""
        return cls(
            polymer_id=data["polymer_id"],
            log_permeability=data["log_permeability"],
            source=data.get("source", "Unknown"),
            temperature=data.get("temperature"),
            pressure=data.get("pressure"),
            gas_species=data.get("gas_species"),
            metadata=data.get("metadata", {})
        )