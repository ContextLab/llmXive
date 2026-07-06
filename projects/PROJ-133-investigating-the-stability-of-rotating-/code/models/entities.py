"""
Core data models for the Rotating Bose-Einstein Condensate simulation pipeline.

This module defines the primary dataclasses used to represent simulation runs
and the resulting stability metrics.

Per spec amendment FR-004 (T021b), StabilityMetric uses `vortex_density`
instead of the previously specified retention fraction.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np

@dataclass
class SimulationRun:
    """
    Represents a single execution of the GPE solver with specific parameters.

    Attributes:
        run_id: Unique identifier for this run (usually derived from seed or hash).
        rotation_rate (Omega): Rotation frequency of the trap (rad/s).
        dipolar_strength (epsilon_dd): Strength of dipolar interactions.
        atom_count (N): Number of atoms in the condensate.
        grid_size: Tuple (Nx, Ny) representing the simulation grid dimensions.
        seed: Random seed used for initialization.
        timestamp: ISO format timestamp of when the run was configured.
        status: Current status of the run ('pending', 'running', 'completed', 'failed').
        error_message: Optional error message if status is 'failed'.
        output_path: Relative path to the saved simulation data (density/phase snapshots).
        metadata: Dictionary for storing additional runtime parameters or flags.
    """
    run_id: str
    rotation_rate: float
    dipolar_strength: float
    atom_count: int
    grid_size: tuple
    seed: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "rotation_rate": self.rotation_rate,
            "dipolar_strength": self.dipolar_strength,
            "atom_count": self.atom_count,
            "grid_size": list(self.grid_size),
            "seed": self.seed,
            "timestamp": self.timestamp,
            "status": self.status,
            "error_message": self.error_message,
            "output_path": self.output_path,
            **self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRun':
        """Reconstruct a SimulationRun from a dictionary."""
        # Handle grid_size if it comes in as a list from JSON/CSV
        grid = data.get("grid_size")
        if isinstance(grid, list):
            grid = tuple(grid)
        
        return cls(
            run_id=data["run_id"],
            rotation_rate=data["rotation_rate"],
            dipolar_strength=data["dipolar_strength"],
            atom_count=data["atom_count"],
            grid_size=grid,
            seed=data["seed"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            status=data.get("status", "pending"),
            error_message=data.get("error_message"),
            output_path=data.get("output_path"),
            metadata={k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        )


@dataclass
class StabilityMetric:
    """
    Represents the calculated stability metrics for a completed simulation run.

    Per spec amendment FR-004 (T021b), the primary metric is `vortex_density`
    (vortices per unit area) rather than a retention fraction.

    Attributes:
        run_id: Reference to the SimulationRun this metric belongs to.
        vortex_density: Number of vortices detected divided by the simulation area.
        radial_variance: Variance of the density distribution along the radial direction.
        structure_factor_sharpness: A measure of the peakiness of the structure factor,
                                   indicating the degree of ordering.
        is_stable: Boolean flag indicating if the condensate is considered stable
                   (e.g., vortex density below a threshold, or no collapse).
        detection_time: Timestamp when metrics were calculated.
        raw_vortex_count: The integer count of vortices detected before normalization.
        area: The physical area of the simulation domain.
        metadata: Additional analysis details (e.g., threshold used, algorithm version).
    """
    run_id: str
    vortex_density: float
    radial_variance: float
    structure_factor_sharpness: float
    is_stable: bool
    detection_time: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_vortex_count: int = 0
    area: float = 1.0  # Default to 1.0 if not specified, usually calculated from grid
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "vortex_density": self.vortex_density,
            "radial_variance": self.radial_variance,
            "structure_factor_sharpness": self.structure_factor_sharpness,
            "is_stable": self.is_stable,
            "detection_time": self.detection_time,
            "raw_vortex_count": self.raw_vortex_count,
            "area": self.area,
            **self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StabilityMetric':
        """Reconstruct a StabilityMetric from a dictionary."""
        return cls(
            run_id=data["run_id"],
            vortex_density=data["vortex_density"],
            radial_variance=data["radial_variance"],
            structure_factor_sharpness=data["structure_factor_sharpness"],
            is_stable=bool(data["is_stable"]),
            detection_time=data.get("detection_time", datetime.now().isoformat()),
            raw_vortex_count=int(data.get("raw_vortex_count", 0)),
            area=float(data.get("area", 1.0)),
            metadata={k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        )