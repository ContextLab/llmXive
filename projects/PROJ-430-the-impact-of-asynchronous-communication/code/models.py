"""
Data Models for the Research Pipeline.

Defines the core entities used throughout the asynchronous communication analysis:
Project, Event, ContributorPair, PairMetric, and Metric.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    """Enumeration of GitHub event types supported by the pipeline."""
    ISSUE = "issue"
    PR = "pull_request"
    COMMENT = "comment"

@dataclass
class Project:
    """
    Represents a GitHub repository being analyzed.
    
    Attributes:
        id: Unique identifier for the project (e.g., 'owner/repo').
        name: Human-readable name of the project.
        created_at: Timestamp of project creation.
        events: List of all events associated with this project.
        pair_metrics: List of PairMetric objects derived from events.
        project_metrics: Aggregated project-level metrics (e.g., median variance).
    """
    id: str
    name: str
    created_at: Optional[datetime] = None
    events: List['Event'] = field(default_factory=list)
    pair_metrics: List['PairMetric'] = field(default_factory=list)
    project_metrics: Optional[Dict[str, float]] = None

@dataclass
class Event:
    """
    Represents a single interaction event (Issue, PR, or Comment).
    
    Attributes:
        id: Unique identifier for the event.
        project_id: ID of the project this event belongs to.
        type: Type of the event (Issue, PR, Comment).
        author: Username of the event author.
        created_at: Timestamp when the event occurred.
        body: Text content of the event (for comments/issues/PRs).
        parent_id: ID of the parent event if this is a reply (e.g., a comment on a comment).
    """
    id: str
    project_id: str
    type: EventType
    author: str
    created_at: datetime
    body: str = ""
    parent_id: Optional[str] = None

@dataclass
class ContributorPair:
    """
    Represents a unique pair of contributors interacting with each other.
    
    Attributes:
        author_a: Username of the first contributor (lexicographically smaller).
        author_b: Username of the second contributor (lexicographically larger).
    """
    author_a: str
    author_b: str

@dataclass
class PairMetric:
    """
    Represents calculated metrics for a specific ContributorPair.
    
    Attributes:
        pair: The ContributorPair object this metric belongs to.
        mean_delay: Average time (in seconds) between messages in the pair.
        response_time_variance: Variance of the response times in the pair.
        count: Number of interactions recorded for this pair.
    """
    pair: ContributorPair
    mean_delay: float
    response_time_variance: float
    count: int

@dataclass
class Metric:
    """
    Represents a generic calculated metric value.
    
    Attributes:
        name: Name of the metric (e.g., 'cohesion_proxy_score').
        value: The calculated numerical value.
        metadata: Optional dictionary for additional context (e.g., sample size, method).
    """
    name: str
    value: float
    metadata: Optional[Dict[str, Any]] = None