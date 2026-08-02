from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    ISSUE_CREATED = "issue_created"
    ISSUE_COMMENTED = "issue_commented"
    PR_CREATED = "pr_created"
    PR_COMMENTED = "pr_commented"
    PR_MERGED = "pr_merged"

@dataclass
class Project:
    id: str
    name: str
    owner: str
    created_at: datetime
    team_size: int = 0

@dataclass
class Event:
    id: str
    project_id: str
    type: EventType
    author: str
    timestamp: datetime
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContributorPair:
    author_a: str
    author_b: str
    events: List[Event] = field(default_factory=list)

@dataclass
class Metric:
    project_id: str
    pair_key: str
    mean_delay: float
    response_time_variance: float
    cohesion_proxy_score: Optional[float] = None