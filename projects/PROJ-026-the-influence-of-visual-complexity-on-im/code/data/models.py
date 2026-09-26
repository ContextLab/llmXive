"""
Data models and entities for the project.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ImageStimulus(BaseModel):
    """Represents an image stimulus used in the experiment."""
    path: str
    edge_density: float
    entropy: float
    fractal_dim: float
    complexity_category: Optional[str] = None  # 'Low' or 'High'

class ParticipantResponse(BaseModel):
    """Represents a single trial response from a participant."""
    participant_id: str
    session_id: str
    reaction_time: float
    is_correct: bool
    timestamp: datetime

class AggregatedScore(BaseModel):
    """Represents an aggregated D-score for a participant session."""
    participant_id: str
    session_id: str
    d_score: float
    n_trials_valid: int
    status: str  # 'valid', 'excluded', etc.
