"""
Schema for diffusion coefficient results.

Stores the calculated diffusion coefficients, mean squared displacement (MSD)
metrics, and comparison against NIST reference values for a specific
solvent and simulation duration.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class DiffusionResults:
    """
    Represents the results of a diffusion coefficient calculation.
    
    Attributes:
        solvent: Name of the solvent (e.g., 'water', 'ethanol').
        simulation_duration_ns: Duration of the simulation in nanoseconds.
        diffusion_coefficient: Calculated diffusion coefficient (m^2/s).
        scaled_diffusion_coefficient: Diffusion coefficient after applying 
                                     solvent-specific scaling factors.
        r_squared: R^2 value from the linear regression of MSD vs time.
        msd_slope: Slope of the MSD vs time line (used to calculate D).
        intercept: Intercept of the MSD vs time line.
        nist_reference: Reference diffusion coefficient from NIST (m^2/s).
        absolute_error: Absolute difference between calculated and NIST values.
        relative_error: Relative error (absolute_error / nist_reference).
        timestamp: ISO format timestamp of when the result was generated.
        metadata: Additional context or parameters used in the simulation.
    """
    solvent: str
    simulation_duration_ns: float
    diffusion_coefficient: float
    scaled_diffusion_coefficient: float
    r_squared: float
    msd_slope: float
    intercept: float
    nist_reference: float
    absolute_error: float
    relative_error: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return {
            "solvent": self.solvent,
            "simulation_duration_ns": self.simulation_duration_ns,
            "diffusion_coefficient": self.diffusion_coefficient,
            "scaled_diffusion_coefficient": self.scaled_diffusion_coefficient,
            "r_squared": self.r_squared,
            "msd_slope": self.msd_slope,
            "intercept": self.intercept,
            "nist_reference": self.nist_reference,
            "absolute_error": self.absolute_error,
            "relative_error": self.relative_error,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiffusionResults':
        """Create an instance from a dictionary."""
        return cls(**data)
