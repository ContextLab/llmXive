"""
Schema for diffusion coefficient results from MD simulations.

This module defines the data model for storing and validating
diffusion coefficients calculated from Mean Squared Displacement (MSD)
analysis, along with their comparison to experimental NIST references.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from pydantic import BaseModel, Field, field_validator
    from pydantic.config import ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback to dataclasses if pydantic is not installed (though requirements.txt includes it)
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class DiffusionResult(BaseModel):
        """
        Schema for a single diffusion coefficient measurement.
        
        Attributes:
            solvent: Name of the solvent (e.g., 'water', 'ethanol', 'acetone')
            simulation_time_ns: Duration of the simulation in nanoseconds
            calculated_d: Calculated diffusion coefficient (m^2/s)
            nist_d: Reference diffusion coefficient from NIST (m^2/s)
            mae: Mean Absolute Error between calculated and NIST values
                (absolute difference in this context for single point)
            r_squared: R^2 value from linear regression of MSD vs time
            scaling_factor: Solvent-specific scaling factor applied
            timestamp: ISO format timestamp of the calculation
            status: Status of the calculation ('success', 'failed', 'warning')
            message: Optional message detailing status or errors
        """
        model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
        
        solvent: str = Field(..., description="Name of the solvent")
        simulation_time_ns: float = Field(..., ge=0.0, description="Simulation duration in ns")
        calculated_d: float = Field(..., gt=0.0, description="Calculated diffusion coefficient (m^2/s)")
        nist_d: float = Field(..., gt=0.0, description="NIST reference diffusion coefficient (m^2/s)")
        mae: float = Field(..., ge=0.0, description="Mean Absolute Error (m^2/s)")
        r_squared: float = Field(..., ge=0.0, le=1.0, description="R^2 of MSD linearity")
        scaling_factor: float = Field(..., gt=0.0, description="Applied scaling factor")
        timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        status: str = Field(default="success", description="Calculation status")
        message: Optional[str] = Field(None, description="Status message or error details")
        
        @field_validator('solvent')
        @classmethod
        def validate_solvent_name(cls, v: str) -> str:
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if v.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{v}'")
            return v.lower()
        
        @field_validator('r_squared')
        @classmethod
        def validate_r_squared(cls, v: float) -> float:
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"R^2 must be between 0 and 1, got {v}")
            return v
    
    class DiffusionResultsList(BaseModel):
        """Container for a list of DiffusionResult objects."""
        model_config = ConfigDict(extra='forbid')
        
        results: List[DiffusionResult] = Field(default_factory=list)
        generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            """Convert to a list of dictionaries for CSV export."""
            return [r.model_dump() for r in self.results]

else:
    @dataclass
    class DiffusionResult:
        """
        Schema for a single diffusion coefficient measurement (Dataclass fallback).
        """
        solvent: str
        simulation_time_ns: float
        calculated_d: float
        nist_d: float
        mae: float
        r_squared: float
        scaling_factor: float
        timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        status: str = "success"
        message: Optional[str] = None
        
        def __post_init__(self):
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if self.solvent.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{self.solvent}'")
            if not (0.0 <= self.r_squared <= 1.0):
                raise ValueError(f"R^2 must be between 0 and 1, got {self.r_squared}")
            if self.calculated_d <= 0 or self.nist_d <= 0:
                raise ValueError("Diffusion coefficients must be positive")
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                'solvent': self.solvent,
                'simulation_time_ns': self.simulation_time_ns,
                'calculated_d': self.calculated_d,
                'nist_d': self.nist_d,
                'mae': self.mae,
                'r_squared': self.r_squared,
                'scaling_factor': self.scaling_factor,
                'timestamp': self.timestamp,
                'status': self.status,
                'message': self.message
            }
    
    @dataclass
    class DiffusionResultsList:
        """Container for a list of DiffusionResult objects (Dataclass fallback)."""
        results: List[DiffusionResult] = field(default_factory=list)
        generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            return [r.to_dict() for r in self.results]
