"""
Schema for bootstrap statistical analysis results.

This module defines the data model for storing confidence intervals
and summary statistics derived from bootstrap resampling of MAE distributions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from pydantic import BaseModel, Field, field_validator
    from pydantic.config import ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class BootstrapStats(BaseModel):
        """
        Schema for bootstrap statistics of a specific solvent-timescale combination.
        
        Attributes:
            solvent: Name of the solvent
            simulation_time_ns: Duration of the simulation in nanoseconds
            mean_mae: Mean of the bootstrapped MAE distribution
            std_mae: Standard deviation of the bootstrapped MAE distribution
            ci_lower_95: Lower bound of the 95% confidence interval
            ci_upper_95: Upper bound of the 95% confidence interval
            n_iterations: Number of bootstrap iterations performed
            fallback_triggered: Whether the iteration count was reduced due to time limits
            timestamp: ISO format timestamp of the analysis
        """
        model_config = ConfigDict(extra='forbid')
        
        solvent: str = Field(..., description="Name of the solvent")
        simulation_time_ns: float = Field(..., ge=0.0, description="Simulation duration in ns")
        mean_mae: float = Field(..., ge=0.0, description="Mean MAE (m^2/s)")
        std_mae: float = Field(..., ge=0.0, description="Std Dev of MAE (m^2/s)")
        ci_lower_95: float = Field(..., ge=0.0, description="95% CI Lower Bound (m^2/s)")
        ci_upper_95: float = Field(..., ge=0.0, description="95% CI Upper Bound (m^2/s)")
        n_iterations: int = Field(..., gt=0, description="Number of bootstrap iterations")
        fallback_triggered: bool = Field(default=False, description="Whether fallback to lower iterations occurred")
        timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        
        @field_validator('solvent')
        @classmethod
        def validate_solvent_name(cls, v: str) -> str:
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if v.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{v}'")
            return v.lower()
        
        @field_validator('ci_lower_95', 'ci_upper_95')
        @classmethod
        def validate_ci_bounds(cls, v: float, info) -> float:
            # Note: info is not used here, but kept for future validation logic
            if v < 0:
                raise ValueError("Confidence interval bounds must be non-negative")
            return v
    
    class BootstrapStatsList(BaseModel):
        """Container for a list of BootstrapStats objects."""
        model_config = ConfigDict(extra='forbid')
        
        stats: List[BootstrapStats] = Field(default_factory=list)
        generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            """Convert to a list of dictionaries for CSV export."""
            return [s.model_dump() for s in self.stats]

else:
    @dataclass
    class BootstrapStats:
        """
        Schema for bootstrap statistics (Dataclass fallback).
        """
        solvent: str
        simulation_time_ns: float
        mean_mae: float
        std_mae: float
        ci_lower_95: float
        ci_upper_95: float
        n_iterations: int
        fallback_triggered: bool = False
        timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def __post_init__(self):
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if self.solvent.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{self.solvent}'")
            if self.mean_mae < 0 or self.std_mae < 0:
                raise ValueError("MAE statistics must be non-negative")
            if self.ci_lower_95 < 0 or self.ci_upper_95 < 0:
                raise ValueError("CI bounds must be non-negative")
            if self.n_iterations <= 0:
                raise ValueError("Number of iterations must be positive")
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                'solvent': self.solvent,
                'simulation_time_ns': self.simulation_time_ns,
                'mean_mae': self.mean_mae,
                'std_mae': self.std_mae,
                'ci_lower_95': self.ci_lower_95,
                'ci_upper_95': self.ci_upper_95,
                'n_iterations': self.n_iterations,
                'fallback_triggered': self.fallback_triggered,
                'timestamp': self.timestamp
            }
    
    @dataclass
    class BootstrapStatsList:
        """Container for a list of BootstrapStats objects (Dataclass fallback)."""
        stats: List[BootstrapStats] = field(default_factory=list)
        generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            return [s.to_dict() for s in self.stats]
