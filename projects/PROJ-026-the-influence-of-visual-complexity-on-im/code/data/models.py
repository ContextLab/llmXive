from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageStimulus(BaseModel):
    """Model for image stimulus metadata."""
    path: str
    edge_density: Optional[float] = None
    entropy: Optional[float] = None
    fractal_dim: Optional[float] = None
    session_id: str
    participant_id: str
    status: str = 'pending'


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
    d_score: Optional[float] = None
    n_trials_valid: int = 0
    status: str = 'pending'
    complexity_condition: Optional[str] = None


if __name__ == "__main__":
    # Demo usage
    stimulus = ImageStimulus(
        path="data/raw/stimuli/test.jpg",
        session_id="session_1",
        participant_id="participant_001"
    )
    print(stimulus.model_dump_json(indent=2))