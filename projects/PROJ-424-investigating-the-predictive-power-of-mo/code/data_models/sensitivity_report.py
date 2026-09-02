"""
Schema for sensitivity analysis reports.

This module defines the data model for storing results from the
sensitivity analysis of regression start times on diffusion coefficient
calculations.
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
    class SensitivityReport(BaseModel):
        """
        Schema for a single sensitivity analysis result.
        
        Attributes:
            solvent: Name of the solvent
            simulation_time_ns: Total simulation duration in ns
            start_time_fractions: List of start time fractions tested (e.g., [0.1, 0.2, 0.3])
            calculated_d_values: List of diffusion coefficients calculated for each start time
            variance_percentage: Variance of calculated D values as a percentage of the mean
            variance_passed: Boolean indicating if variance is < 5% (threshold)
            status: Status of the analysis ('success', 'warning', 'failed')
            message: Optional message detailing results or issues
            timestamp: ISO format timestamp
        """
        model_config = ConfigDict(extra='forbid')
        
        solvent: str = Field(..., description="Name of the solvent")
        simulation_time_ns: float = Field(..., ge=0.0, description="Simulation duration in ns")
        start_time_fractions: List[float] = Field(..., description="List of start time fractions")
        calculated_d_values: List[float] = Field(..., description="List of calculated D values")
        variance_percentage: float = Field(..., ge=0.0, description="Variance as percentage of mean")
        variance_passed: bool = Field(..., description="True if variance < 5%")
        status: str = Field(default="success", description="Analysis status")
        message: Optional[str] = Field(None, description="Status message")
        timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        
        @field_validator('solvent')
        @classmethod
        def validate_solvent_name(cls, v: str) -> str:
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if v.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{v}'")
            return v.lower()
        
        @field_validator('start_time_fractions')
        @classmethod
        def validate_fractions(cls, v: List[float]) -> List[float]:
            if not v:
                raise ValueError("Start time fractions cannot be empty")
            for f in v:
                if not (0.0 < f < 1.0):
                    raise ValueError(f"Start time fractions must be between 0 and 1 (exclusive), got {f}")
            return v
        
        @field_validator('calculated_d_values')
        @classmethod
        def validate_d_values(cls, v: List[float], info) -> List[float]:
            if not v:
                raise ValueError("Calculated D values cannot be empty")
            if len(v) != len(info.data.get('start_time_fractions', [])):
                raise ValueError("Length of D values must match length of start time fractions")
            for d in v:
                if d <= 0:
                    raise ValueError("Diffusion coefficients must be positive")
            return v
    
    class SensitivityReportList(BaseModel):
        """Container for a list of SensitivityReport objects."""
        model_config = ConfigDict(extra='forbid')
        
        reports: List[SensitivityReport] = Field(default_factory=list)
        generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            """Convert to a list of dictionaries for CSV/JSON export."""
            return [r.model_dump() for r in self.reports]

else:
    @dataclass
    class SensitivityReport:
        """
        Schema for a single sensitivity analysis result (Dataclass fallback).
        """
        solvent: str
        simulation_time_ns: float
        start_time_fractions: List[float]
        calculated_d_values: List[float]
        variance_percentage: float
        variance_passed: bool
        status: str = "success"
        message: Optional[str] = None
        timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def __post_init__(self):
            valid_solvents = {'water', 'ethanol', 'acetone'}
            if self.solvent.lower() not in valid_solvents:
                raise ValueError(f"Solvent must be one of {valid_solvents}, got '{self.solvent}'")
            
            if not self.start_time_fractions:
                raise ValueError("Start time fractions cannot be empty")
            
            if not self.calculated_d_values:
                raise ValueError("Calculated D values cannot be empty")
            
            if len(self.start_time_fractions) != len(self.calculated_d_values):
                raise ValueError("Length of D values must match length of start time fractions")
            
            for f in self.start_time_fractions:
                if not (0.0 < f < 1.0):
                    raise ValueError(f"Start time fractions must be between 0 and 1 (exclusive), got {f}")
            
            for d in self.calculated_d_values:
                if d <= 0:
                    raise ValueError("Diffusion coefficients must be positive")
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                'solvent': self.solvent,
                'simulation_time_ns': self.simulation_time_ns,
                'start_time_fractions': self.start_time_fractions,
                'calculated_d_values': self.calculated_d_values,
                'variance_percentage': self.variance_percentage,
                'variance_passed': self.variance_passed,
                'status': self.status,
                'message': self.message,
                'timestamp': self.timestamp
            }
    
    @dataclass
    class SensitivityReportList:
        """Container for a list of SensitivityReport objects (Dataclass fallback)."""
        reports: List[SensitivityReport] = field(default_factory=list)
        generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        
        def to_dict_list(self) -> List[Dict[str, Any]]:
            return [r.to_dict() for r in self.reports]
