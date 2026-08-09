"""
Data Models for the Research Pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    ISSUE = "issue"
    PR = "pull_request"
    COMMENT = "comment"

@dataclass
class Project:
    id: str
    name: str
    created_at: Optional[datetime] = None
    events: List['Event'] = field(default_factory=list)
    pair_metrics: List['PairMetric'] = field(default_factory=list)
    project_metrics: Optional[Dict[str, float]] = None

@dataclass
class Event:
    id: str
    project_id: str
    type: EventType
    author: str
    created_at: datetime
    body: str = ""
    parent_id: Optional[str] = None

@dataclass
class ContributorPair:
    author_a: str
    author_b: str

@dataclass
class PairMetric:
    pair: ContributorPair
    mean_delay: float
    response_time_variance: float
    count: int

@dataclass
class Metric:
    name: str
    value: float
    metadata: Optional[Dict[str, Any]] = None
