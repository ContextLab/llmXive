from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class StoryDocument:
    """Data model for a story document."""
    story_id: str
    text: str
    perspective_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReaderResponse:
    """Data model for a reader response."""
    response_id: str
    story_id: str
    empathy_score: float
    moral_judgement_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
