"""
Schema for sensitivity analysis reports.

Stores results from sweeping regression start times to assess the robustness
of the diffusion coefficient calculation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class SensitivityPoint:
    """A single data point in the sensitivity sweep."""
    start_time_fraction: float
    diffusion_coefficient: float
    r_squared: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time_fraction": self.start_time_fraction,
            "diffusion_coefficient": self.diffusion_coefficient,
            "r_squared": self.r_squared
        }

@dataclass
class SensitivityReport:
    """
    Represents the full sensitivity analysis report.
    
    Attributes:
        solvent: Name of the solvent analyzed.
        simulation_duration_ns: Duration of the simulation in nanoseconds.
        sweep_points: List of sensitivity points (start time fractions vs D).
        variance_percentage: Variance of diffusion coefficients across the sweep.
        is_robust: Boolean flag indicating if variance < 5% (per spec).
        timestamp: ISO format timestamp of when the report was generated.
        metadata: Additional context (e.g., sweep range, force field).
    """
    solvent: str
    simulation_duration_ns: float
    sweep_points: List[SensitivityPoint]
    variance_percentage: float
    is_robust: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return {
            "solvent": self.solvent,
            "simulation_duration_ns": self.simulation_duration_ns,
            "sweep_points": [p.to_dict() for p in self.sweep_points],
            "variance_percentage": self.variance_percentage,
            "is_robust": self.is_robust,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensitivityReport':
        """Create an instance from a dictionary."""
        # Reconstruct nested objects
        sweep_points = [
            SensitivityPoint(
                start_time_fraction=p["start_time_fraction"],
                diffusion_coefficient=p["diffusion_coefficient"],
                r_squared=p["r_squared"]
            )
            for p in data.get("sweep_points", [])
        ]
        
        return cls(
            solvent=data["solvent"],
            simulation_duration_ns=data["simulation_duration_ns"],
            sweep_points=sweep_points,
            variance_percentage=data["variance_percentage"],
            is_robust=data["is_robust"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {})
        )