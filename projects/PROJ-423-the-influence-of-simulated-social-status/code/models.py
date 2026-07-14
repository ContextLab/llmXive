from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class StatusLevel(str, Enum):
    HIGH = "High"
    LOW = "Low"

class ObservedBehavior(str, Enum):
    RISKY = "Risky"
    CONSERVATIVE = "Conservative"

class Participant(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    participant_id: str
    status_level: StatusLevel
    observed_behavior: ObservedBehavior
    risk_taking_score: float
    timestamp: Optional[datetime] = None

class Condition(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    condition_id: str
    status_level: StatusLevel
    observed_behavior: ObservedBehavior
    mean_risk_score: float
    n_participants: int

class ModelResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_type: str
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    vif_scores: Optional[Dict[str, float]] = None
    interaction_p_value: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
