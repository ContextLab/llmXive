"""
Base data models for the plant stress resilience prediction pipeline.

Defines Pydantic models for MetabolomicProfile, RecoveryMetric, and RecoveryIndex
with validation rules as per project specifications.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re


class StressType(str, Enum):
    """Enumeration of supported stress types."""
    DROUGHT = "drought"
    HEAT = "heat"
    COLD = "cold"
    SALINITY = "salinity"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    PATHOGEN = "pathogen"
    OTHER = "other"


class RecoveryMetric(BaseModel):
    """
    Represents a single recovery measurement for a plant sample.
    
    Attributes:
        sample_id: Unique identifier for the plant sample.
        stress_type: Type of stress applied (from StressType enum).
        days_post_stress: Number of days after stress application.
        biomass_change: Relative change in biomass (post-stress / pre-stress).
        survival_status: Binary indicator (1=survived, 0=dead).
        recovery_score: Optional continuous recovery score (0-1 scale).
        metadata: Additional experimental details.
    """
    sample_id: str = Field(..., min_length=1, description="Unique sample identifier")
    stress_type: StressType
    days_post_stress: int = Field(..., ge=0, description="Days after stress application")
    biomass_change: Optional[float] = Field(None, ge=0, description="Relative biomass change")
    survival_status: Optional[int] = Field(None, ge=0, le=1, description="Survival status (0 or 1)")
    recovery_score: Optional[float] = Field(None, ge=0, le=1, description="Normalized recovery score")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def check_recovery_data_exists(self):
        """Ensure at least one recovery metric is provided."""
        if (
            self.biomass_change is None and 
            self.survival_status is None and 
            self.recovery_score is None
        ):
            raise ValueError(
                "At least one of biomass_change, survival_status, or recovery_score must be provided."
            )
        return self


class MetabolomicProfile(BaseModel):
    """
    Represents a metabolomic profile for a plant sample.
    
    Attributes:
        sample_id: Unique identifier matching the recovery metric.
        stress_type: Type of stress applied.
        timepoint: Time of sample collection relative to stress (e.g., 'pre', 'post_7d').
        metabolite_data: Dictionary mapping metabolite names to concentrations.
        metadata: Experimental context (species, tissue type, etc.).
    """
    sample_id: str = Field(..., min_length=1, description="Unique sample identifier")
    stress_type: StressType
    timepoint: str = Field(..., min_length=1, description="Sample collection timepoint")
    metabolite_data: Dict[str, float] = Field(..., description="Metabolite name -> concentration")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('metabolite_data')
    @classmethod
    def metabolites_must_be_positive(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure all metabolite concentrations are non-negative."""
        for name, value in v.items():
            if value < 0:
                raise ValueError(f"Metabolite '{name}' has negative concentration: {value}")
        return v

    @model_validator(mode='after')
    def check_metabolites_not_empty(self):
        """Ensure metabolite data is not empty."""
        if not self.metabolite_data:
            raise ValueError("metabolite_data cannot be empty.")
        return self


class RecoveryIndex(BaseModel):
    """
    A unified, normalized recovery index (0-1 scale) derived from raw metrics.
    
    Attributes:
        sample_id: Unique identifier.
        index_value: Normalized recovery score (0 = no recovery, 1 = full recovery).
        source_metric: The original metric used for calculation (e.g., 'biomass', 'survival').
        calculation_method: Description of how the index was derived.
    """
    sample_id: str = Field(..., min_length=1)
    index_value: float = Field(..., ge=0, le=1, description="Normalized recovery index (0-1)")
    source_metric: str = Field(..., description="Original metric source")
    calculation_method: str = Field(..., description="Method used for normalization")

    @field_validator('index_value')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure index is strictly within [0, 1]."""
        if v < 0 or v > 1:
            raise ValueError(f"Recovery index must be between 0 and 1, got {v}")
        return v