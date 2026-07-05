"""Pydantic schemas for data validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import math

class StudySchema(BaseModel):
    """Schema for individual study data."""
    study_id: str = Field(..., description="Unique identifier for the study")
    effect_size: float = Field(..., ge=-10, le=10, description="Effect size value")
    standard_error: float = Field(..., gt=0, description="Standard error (must be positive)")
    sample_size: Optional[int] = Field(None, ge=1, description="Sample size")
    
    @field_validator('standard_error')
    @classmethod
    def check_positive_se(cls, v):
        if v <= 0:
            raise ValueError('Standard error must be positive')
        return v
        
class SubsampleSchema(BaseModel):
    """Schema for a bootstrap subsample."""
    subsample_id: str = Field(..., description="Unique identifier for the subsample")
    meta_id: str = Field(..., description="Parent meta-analysis ID")
    k: int = Field(..., ge=2, description="Number of studies in subsample")
    seed: int = Field(..., description="Random seed used")
    estimator_type: str = Field(..., description="Estimator type (e.g., REML, DL)")
    studies: List[StudySchema] = Field(..., min_length=1, description="List of studies in subsample")
    pooled_effect: Optional[float] = Field(None, description="Pooled effect size")
    pooled_se: Optional[float] = Field(None, description="Pooled standard error")
    
class MetaAnalysisSchema(BaseModel):
    """Schema for a complete meta-analysis."""
    meta_id: str = Field(..., description="Unique identifier for the meta-analysis")
    title: str = Field(..., min_length=1, description="Title of the meta-analysis")
    source: str = Field(..., description="Source database or publication")
    studies: List[StudySchema] = Field(..., min_length=2, description="List of studies")
    full_sample_effect: Optional[float] = Field(None, description="Full sample pooled effect")
    full_sample_se: Optional[float] = Field(None, description="Full sample pooled SE")
    
    @model_validator(mode='after')
    def validate_studies(self):
        if len(self.studies) < 2:
            raise ValueError("Meta-analysis must have at least 2 studies")
        return self
        
class StabilityMetricSchema(BaseModel):
    """Schema for stability metrics."""
    meta_id: str = Field(..., description="Meta-analysis ID")
    k: int = Field(..., ge=2, description="Number of studies")
    model_type: str = Field(..., description="Model type used")
    sd_effects: float = Field(..., ge=0, description="Standard deviation of effects")
    coverage_rate: float = Field(..., ge=0, le=1, description="CI coverage rate")
    threshold_reached: bool = Field(False, description="Whether stability threshold reached")
    changepoint_estimate: Optional[float] = Field(None, description="Estimated changepoint")
    
    @field_validator('coverage_rate')
    @classmethod
    def check_coverage_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Coverage rate must be between 0 and 1')
        return v