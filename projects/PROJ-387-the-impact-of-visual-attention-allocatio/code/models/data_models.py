from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re

class ValenceCategory(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class EyeTrackingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    participant_id: str
    timestamp: datetime
    fixation_duration: float
    saccade_amplitude: float
    gaze_distribution: Dict[str, float]
    track_loss: float
    calibrated: bool

class RecallScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    participant_id: str
    passage_id: str
    score: float
    valence_label: ValenceCategory

class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric: str
    valence: ValenceCategory
    coef: float
    p_raw: float
    p_corrected: Optional[float] = None
    association_label: str = "associational"

class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset: str
    valid: bool
    missing_columns: List[str] = []
    track_loss: float = 0.0
    valence_valid: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)
