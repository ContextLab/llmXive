from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Participant:
    id: str
    condition: str
    timestamp: datetime = field(default_factory=datetime.now)
    responses: List['Response'] = field(default_factory=list)

@dataclass
class Response:
    id: str
    question_id: str
    value: str
    timestamp: datetime = field(default_factory=datetime.now)
