from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ImageStimulus(BaseModel):
    """Model for image stimulus metadata."""
    path: str
    edge_density: float
    entropy: float
    fractal_dim: float

class ParticipantResponse(BaseModel):
    """Model for participant response data."""
    participant_id: str
    session_id: str
    reaction_time: float
    is_correct: bool
    timestamp: datetime

class AggregatedScore(BaseModel):
    """Model for aggregated D-score per session."""
    participant_id: str
    session_id: str
    d_score: float
    n_trials_valid: int
    status: str
