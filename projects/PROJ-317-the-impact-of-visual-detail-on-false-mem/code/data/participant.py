from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Participant:
    id: str
    condition: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Response:
    id: str
    question_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    participant_id: Optional[str] = None
    is_lure: bool = False