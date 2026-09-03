"""
SimulationBox model for amorphous solid heat conduction studies.

Defines the core data structure for atomic positions, velocities,
simulation box metadata, and thermal conductivity values.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class SimulationBox:
    """
    Represents a simulation box containing atomic data for amorphous solids.

    Attributes:
        atom_ids: List of unique integer identifiers for atoms.
        positions: (N, 3) numpy array of atomic positions in Angstroms.
        velocities: (N, 3) numpy array of atomic velocities in Angstrom/ps.
        box_vectors: (3, 3) numpy array defining the simulation cell vectors.
        metadata: Dictionary for simulation parameters (temperature, time_step, etc.).
        thermal_conductivity: Optional scalar thermal conductivity value (W/m·K).
    """
    atom_ids: List[int]
    positions: np.ndarray
    velocities: Optional[np.ndarray] = None
    box_vectors: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    thermal_conductivity: Optional[float] = None

    def __post_init__(self):
        """Validate shapes and consistency of input data."""
        # Ensure positions are numpy array
        if not isinstance(self.positions, np.ndarray):
            self.positions = np.array(self.positions, dtype=np.float64)
        
        # Validate position shape
        if self.positions.ndim != 2 or self.positions.shape[1] != 3:
            raise ValueError(
                f"Positions must be an (N, 3) array. Got shape: {self.positions.shape}"
            )

        n_atoms = len(self.atom_ids)
        
        # Validate atom_ids count matches positions
        if len(self.atom_ids) != n_atoms:
            raise ValueError(
                f"Number of atom_ids ({len(self.atom_ids)}) must match number of positions ({n_atoms})"
            )

        # Validate velocities if provided
        if self.velocities is not None:
            if not isinstance(self.velocities, np.ndarray):
                self.velocities = np.array(self.velocities, dtype=np.float64)
            
            if self.velocities.shape != self.positions.shape:
                raise ValueError(
                    f"Velocities shape {self.velocities.shape} must match positions shape {self.positions.shape}"
                )

        # Validate box_vectors if provided
        if self.box_vectors is not None:
            if not isinstance(self.box_vectors, np.ndarray):
                self.box_vectors = np.array(self.box_vectors, dtype=np.float64)
            
            if self.box_vectors.shape != (3, 3):
                raise ValueError(
                    f"Box vectors must be a (3, 3) array. Got shape: {self.box_vectors.shape}"
                )

    def get_kinetic_energy(self) -> Optional[float]:
        """
        Calculate total kinetic energy of the system.

        Returns:
            Total kinetic energy in eV, or None if velocities are not available.
        """
        if self.velocities is None:
            return None

        # v in Angstrom/ps -> need to convert to consistent units for KE
        # Assuming standard atomic mass units for simplicity, or generic scaling
        # KE = 0.5 * m * v^2. If m is not provided, we return the sum of v^2 * 0.5
        # Note: In a full physics implementation, atomic masses would be required.
        # Here we return the scalar velocity sum squared * 0.5 as a proxy metric
        # unless specific masses are added to metadata.
        v_squared = np.sum(self.velocities ** 2, axis=1)
        return float(np.sum(v_squared) * 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the SimulationBox to a dictionary representation.

        Returns:
            Dictionary containing all attributes with numpy arrays converted to lists.
        """
        return {
            "atom_ids": self.atom_ids,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist() if self.velocities is not None else None,
            "box_vectors": self.box_vectors.tolist() if self.box_vectors is not None else None,
            "metadata": self.metadata,
            "thermal_conductivity": self.thermal_conductivity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationBox":
        """
        Create a SimulationBox instance from a dictionary.

        Args:
            data: Dictionary containing SimulationBox attributes.

        Returns:
            A new SimulationBox instance.
        """
        return cls(
            atom_ids=data["atom_ids"],
            positions=np.array(data["positions"]),
            velocities=np.array(data["velocities"]) if data.get("velocities") is not None else None,
            box_vectors=np.array(data["box_vectors"]) if data.get("box_vectors") is not None else None,
            metadata=data.get("metadata", {}),
            thermal_conductivity=data.get("thermal_conductivity")
        )

    def __len__(self) -> int:
        """Return the number of atoms in the simulation box."""
        return len(self.atom_ids)

    def __repr__(self) -> str:
        """String representation of the SimulationBox."""
        return (
            f"SimulationBox(n_atoms={len(self)}, "
            f"box_vectors={self.box_vectors.shape if self.box_vectors is not None else None}, "
            f"has_velocities={self.velocities is not None})"
        )
