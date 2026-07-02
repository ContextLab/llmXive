from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import json

class Subject(BaseModel):
    id: str
    genre_scores: Dict[str, float]

class TimeSeries(BaseModel):
    roi_id: str
    values: List[float]

class NetworkMetric(BaseModel):
    subject_id: str
    metric_name: str
    value: float

class CorrelationResult(BaseModel):
    metric: str
    genre: str
    r: float
    p_raw: float
    p_adj: float

class SensitivityReport(BaseModel):
    window_size: int
    icc: float
