from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class StoryDocument:
    story_id: str
    raw_text: str
    perspective_score: float
    confidence_flag: str

@dataclass
class ReaderResponse:
    story_id: str
    participant_id: str
    empathy_score: float
    moral_judgement_score: float
    timestamp: datetime = field(default_factory=datetime.now)
