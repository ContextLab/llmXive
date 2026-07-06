"""
Atomic configuration data model for amorphous silicon network analysis.

This module defines the core data structures for representing atomic
configurations, including coordinates, species, and metadata required
for graph construction and property analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

@dataclass
class AtomicConfiguration:
    """
    Represents a single atomic configuration of amorphous silicon.

    Attributes:
        config_id: Unique identifier for this configuration.
        positions: Array of atomic positions (N x 3) in Angstroms.
        species: List of atomic species (e.g., 'Si') for each atom.
        box_size: Optional tuple (Lx, Ly, Lz) defining the simulation box.
        source: Origin of the data (e.g., 'Zenodo-12345', 'MD-Simulation-X').
        source_url: URL where the raw data was retrieved from.
        timestamp: ISO format timestamp of when the data was processed.
        metadata: Additional arbitrary metadata dictionary.
    """
    config_id: str
    positions: np.ndarray
    species: List[str]
    box_size: Optional[Tuple[float, float, float]] = None
    source: str = "unknown"
    source_url: str = ""
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize the configuration data."""
        # Ensure positions is a numpy array
        if not isinstance(self.positions, np.ndarray):
            self.positions = np.array(self.positions, dtype=np.float64)
        
        # Validate shape: must be (N, 3)
        if self.positions.ndim != 2 or self.positions.shape[1] != 3:
            raise ValueError(f"Positions must be an (N, 3) array, got {self.positions.shape}")

        # Ensure species list length matches number of atoms
        n_atoms = len(self.positions)
        if len(self.species) != n_atoms:
            raise ValueError(f"Number of species ({len(self.species)}) must match number of atoms ({n_atoms})")

        # Validate species types (currently assuming all are strings)
        if not all(isinstance(s, str) for s in self.species):
            raise ValueError("All species must be strings")

    @property
    def n_atoms(self) -> int:
        """Return the number of atoms in the configuration."""
        return len(self.positions)

    @property
    def atomic_numbers(self) -> np.ndarray:
        """
        Return a numpy array of atomic numbers corresponding to the species.
        
        Currently supports 'Si' (Silicon).
        """
        element_map = {
            'Si': 14,
            'C': 6,
            'H': 1,
            'O': 8,
            'N': 7
        }
        try:
            return np.array([element_map.get(s.upper(), 0) for s in self.species], dtype=int)
        except KeyError as e:
            raise ValueError(f"Unknown element in species list: {e}")

    def get_element_counts(self) -> Dict[str, int]:
        """Return a dictionary counting occurrences of each element."""
        counts: Dict[str, int] = {}
        for s in self.species:
            key = s.upper()
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary representation."""
        return {
            'config_id': self.config_id,
            'positions': self.positions.tolist(),
            'species': self.species,
            'box_size': self.box_size,
            'source': self.source,
            'source_url': self.source_url,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'n_atoms': self.n_atoms
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AtomicConfiguration':
        """
        Create an AtomicConfiguration instance from a dictionary.
        
        Args:
            data: Dictionary containing configuration data.
            
        Returns:
            AtomicConfiguration instance.
        """
        positions = np.array(data['positions'], dtype=np.float64)
        species = data['species']
        
        # Handle optional fields
        box_size = data.get('box_size')
        if box_size and len(box_size) == 3:
            box_size = tuple(box_size)
        
        return cls(
            config_id=data['config_id'],
            positions=positions,
            species=species,
            box_size=box_size,
            source=data.get('source', 'unknown'),
            source_url=data.get('source_url', ''),
            timestamp=data.get('timestamp'),
            metadata=data.get('metadata', {})
        )

    def __repr__(self) -> str:
        element_counts = self.get_element_counts()
        elements_str = ", ".join([f"{k}: {v}" for k, v in element_counts.items()])
        return (
            f"AtomicConfiguration(id={self.config_id}, "
            f"n_atoms={self.n_atoms}, "
            f"elements=[{elements_str}], "
            f"source={self.source})"
        )
