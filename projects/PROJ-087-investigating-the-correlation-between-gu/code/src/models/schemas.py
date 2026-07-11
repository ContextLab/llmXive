"""
Pydantic models for data validation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
import json

class SleepMetric(BaseModel):
    sample_id: str
    sleep_efficiency: float
    sleep_duration_hours: float
    wake_after_sleep_onset: Optional[float] = None

class MicrobiomeSample(BaseModel):
    sample_id: str
    shannon_diversity: float
    simpson_diversity: float
    observed_otus: int
    antibiotic_use_last_3m: bool = False

class CorrelationResult(BaseModel):
    metric_diversity: str
    metric_sleep: str
    r: float
    p: float
    q: Optional[float] = None
    is_moderate: bool = False
    is_meaningful: bool = False

def models_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model to a dictionary."""
    return model.model_dump()
