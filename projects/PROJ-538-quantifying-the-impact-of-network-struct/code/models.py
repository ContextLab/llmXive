from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import numpy as np

class AtomicSnapshot(BaseModel):
    positions: List[List[float]]
    species: List[str]
    thermal_conductivity: float

    @field_validator('positions')
    def check_positions(cls, v):
        if not v:
            raise ValueError("Positions cannot be empty")
        return v

class DefectGraph(BaseModel):
    nodes: List[int]
    edges: List[tuple]
    metrics: Dict[str, float]

class CorrelationResult(BaseModel):
    metric_name: str
    correlation_coefficient: float
    p_value: float
    corrected_p_value: float
    significance: bool

class SensitivityResult(BaseModel):
    threshold: float
    correlation_coefficient: float
    p_value: float
    magnitude_difference: float
    rank_stability_metric: float
    rank_stability_flag: str
    consistency_flag: str

class PowerAnalysisResult(BaseModel):
    minimum_detectable_effect_size: float
    power: float
    sample_size: int
    alpha: float