from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
import json

class SleepMetric(BaseModel):
    sample_id: str
    sleep_efficiency: float = Field(..., ge=0.0, le=1.0)
    sleep_duration_hours: float = Field(..., ge=0.0, le=24.0)
    antibiotic_use_last_3m: bool

    @field_validator('sleep_efficiency')
    @classmethod
    def validate_efficiency(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('Sleep efficiency must be between 0 and 1')
        return v

class MicrobiomeSample(BaseModel):
    sample_id: str
    otu_counts: Dict[str, int]
    sequencing_depth: int

    @field_validator('otu_counts')
    @classmethod
    def validate_otu_counts(cls, v):
        for k, val in v.items():
            if val < 0:
                raise ValueError(f'OTU count for {k} cannot be negative')
        return v

class CorrelationResult(BaseModel):
    metric_1: str
    metric_2: str
    spearman_r: float
    p_value: float
    q_value: float
    is_moderate: bool
    is_meaningful: bool

    class Config:
        json_schema_extra = {
            "example": {
                "metric_1": "shannon",
                "metric_2": "sleep_efficiency",
                "spearman_r": 0.35,
                "p_value": 0.01,
                "q_value": 0.03,
                "is_moderate": True,
                "is_meaningful": True
            }
        }

def models_to_dict(model: Any) -> Dict[str, Any]:
    """Convert Pydantic model to dictionary."""
    return model.model_dump()
