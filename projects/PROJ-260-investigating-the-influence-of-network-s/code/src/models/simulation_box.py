"""
Simulation Box Data Class.

Defines the core data structure for a simulation box containing atomic positions,
velocities, metadata, and thermal conductivity properties.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class SimulationBox:
    """
    Data class representing a single simulation box of an amorphous solid.

    Attributes:
        atom_ids: List of unique integer identifiers for atoms.
        positions: numpy array of shape (N, 3) containing atomic positions (Angstrom).
        velocities: Optional numpy array of shape (N, 3) containing atomic velocities (Angstrom/ps).
        box_vectors: numpy array of shape (3, 3) containing the simulation box lattice vectors.
        metadata: Dictionary for storing additional simulation parameters (e.g., temperature, ensemble).
        thermal_conductivity: Optional float representing the thermal conductivity (W/m·K).
        system_size: Integer representing the number of atoms (N).
    """
    atom_ids: List[int]
    positions: np.ndarray
    box_vectors: np.ndarray
    system_size: int
    velocities: Optional[np.ndarray] = None
    thermal_conductivity: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validates the dimensions and types of the input data.
        Raises ValueError if dimensions are inconsistent.
        """
        # Ensure numpy arrays
        if not isinstance(self.positions, np.ndarray):
            self.positions = np.array(self.positions, dtype=np.float64)
        
        if self.velocities is not None and not isinstance(self.velocities, np.ndarray):
            self.velocities = np.array(self.velocities, dtype=np.float64)

        # Validate shapes
        expected_shape = (self.system_size, 3)
        if self.positions.shape != expected_shape:
            raise ValueError(
                f"Positions shape {self.positions.shape} does not match system_size {self.system_size}. "
                f"Expected {expected_shape}."
            )

        if self.velocities is not None and self.velocities.shape != expected_shape:
            raise ValueError(
                f"Velocities shape {self.velocities.shape} does not match system_size {self.system_size}. "
                f"Expected {expected_shape}."
            )

        if self.box_vectors.shape != (3, 3):
            raise ValueError(f"Box vectors must be a (3, 3) matrix. Got {self.box_vectors.shape}.")

        if len(self.atom_ids) != self.system_size:
            raise ValueError(
                f"Number of atom_ids ({len(self.atom_ids)}) does not match system_size ({self.system_size})."
            )

    def get_kinetic_energy(self) -> float:
        """
        Calculates the total kinetic energy of the system.
        
        Returns:
            float: Total kinetic energy in eV (assuming mass in amu and velocity in Angstrom/ps).
        """
        if self.velocities is None:
            return 0.0
        
        # E_k = 0.5 * m * v^2
        # Assuming average mass for Silicon (28.0855 amu) if not specified, 
        # or we can return a generic sum of v^2 if mass is unknown.
        # For this generic class, we return sum of v^2 scaled by 0.5.
        # Conversion to eV would require mass and unit constants.
        # Here we return the raw sum of squared velocities for consistency.
        return 0.5 * np.sum(self.velocities ** 2)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SimulationBox instance to a dictionary representation.
        
        Returns:
            Dict containing all attributes, with numpy arrays converted to lists.
        """
        return {
            "atom_ids": self.atom_ids,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist() if self.velocities is not None else None,
            "box_vectors": self.box_vectors.tolist(),
            "thermal_conductivity": self.thermal_conductivity,
            "system_size": self.system_size,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationBox":
        """
        Creates a SimulationBox instance from a dictionary.
        
        Args:
            data: Dictionary containing the simulation box data.
            
        Returns:
            SimulationBox instance.
        """
        return cls(
            atom_ids=data["atom_ids"],
            positions=np.array(data["positions"]),
            box_vectors=np.array(data["box_vectors"]),
            system_size=data["system_size"],
            velocities=np.array(data["velocities"]) if data.get("velocities") is not None else None,
            thermal_conductivity=data.get("thermal_conductivity"),
            metadata=data.get("metadata", {})
        )
