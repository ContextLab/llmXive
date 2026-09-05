"""
Schema for bootstrap statistics.

Stores aggregated statistical metrics derived from bootstrap resampling
of Mean Absolute Error (MAE) distributions across multiple simulation runs.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class BootstrapStats:
    """
    Represents statistical summary of bootstrap resampling results.
    
    Attributes:
        solvent: Name of the solvent analyzed.
        simulation_duration_ns: Duration of the simulation in nanoseconds.
        mean_mae: Mean of the bootstrap MAE distribution.
        std_mae: Standard deviation of the bootstrap MAE distribution.
        ci_95_lower: Lower bound of the 95% confidence interval.
        ci_95_upper: Upper bound of the 95% confidence interval.
        n_iterations: Number of bootstrap iterations performed.
        nist_reference: NIST reference value used for error calculation.
        timestamp: ISO format timestamp of when the stats were generated.
        metadata: Additional context (e.g., fallback status, seed).
    """
    solvent: str
    simulation_duration_ns: float
    mean_mae: float
    std_mae: float
    ci_95_lower: float
    ci_95_upper: float
    n_iterations: int
    nist_reference: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return {
            "solvent": self.solvent,
            "simulation_duration_ns": self.simulation_duration_ns,
            "mean_mae": self.mean_mae,
            "std_mae": self.std_mae,
            "ci_95_lower": self.ci_95_lower,
            "ci_95_upper": self.ci_95_upper,
            "n_iterations": self.n_iterations,
            "nist_reference": self.nist_reference,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BootstrapStats':
        """Create an instance from a dictionary."""
        return cls(**data)
