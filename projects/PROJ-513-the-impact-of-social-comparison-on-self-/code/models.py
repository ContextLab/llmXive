"""
Data Models.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

class StimulusOrigin(Enum):
    AI = "AI"
    HUMAN = "Human"

@dataclass
class Participant:
    id: str
    incom_score: Optional[int] = None
    usage_frequency: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Stimulus:
    id: str
    origin: StimulusOrigin
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Response:
    participant_id: str
    stimulus_id: str
    origin: StimulusOrigin
    timestamp: datetime
    biss_score: int
    incom_score: Optional[int] = None
    usage_frequency: Optional[float] = None