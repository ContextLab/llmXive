from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ImageStimulus(BaseModel):
    """Model for image stimulus metadata."""
    path: str
    edge_density: float = Field(..., ge=0.0, le=1.0)
    entropy: float = Field(..., ge=0.0)
    fractal_dim: float = Field(..., ge=1.0, le=3.0)

class ParticipantResponse(BaseModel):
    """Model for participant response data."""
    participant_id: str
    session_id: int
    reaction_time: float = Field(..., gt=0.0)
    is_correct: bool
    timestamp: Optional[datetime] = None

class AggregatedScore(BaseModel):
    """Model for aggregated D-score results."""
    participant_id: str
    session_id: int
    d_score: Optional[float] = None
    n_trials_valid: int = Field(..., ge=0)
    status: str = Field(..., pattern="^(valid|insufficient_trials|calculation_failed)$")

if __name__ == "__main__":
    print("Models module loaded.")
