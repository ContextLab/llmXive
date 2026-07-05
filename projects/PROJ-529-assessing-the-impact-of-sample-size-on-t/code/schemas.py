from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

class MetaAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta_id: str
    title: str
    source: str
    effect_sizes: List[float]
    standard_errors: List[float]
    created_at: datetime = Field(default_factory=datetime.now)

class Subsample(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subsample_id: str
    meta_id: str
    k: int
    seed: int
    effect_sizes: List[float]
    standard_errors: List[float]

class StabilityMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str
    meta_id: str
    k: int
    model_type: str
    pooled_effect: float
    sd_effects: float
    coverage_rate: float

def validate_meta_analysis(data: dict) -> MetaAnalysis:
    return MetaAnalysis(**data)

def validate_subsample(data: dict) -> Subsample:
    return Subsample(**data)

def validate_stability_metric(data: dict) -> StabilityMetric:
    return StabilityMetric(**data)
