"""
Data models and entities for the Asynchronous Communication Impact study.

Defines core entities: Project, Event, ContributorPair, and Metric.
These classes provide a structured interface for data ingestion,
metric calculation, and analysis while adhering to the project's
data model specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class EventType(Enum):
    """Enumeration of supported GitHub event types."""
    ISSUES = "issues"
    PULL_REQUEST = "pull_request"
    COMMENT = "comment"
    PUSH = "push"
    OTHER = "other"


@dataclass
class Project:
    """
    Represents a GitHub repository under study.

    Attributes:
        project_id: Unique identifier (e.g., 'owner/repo').
        name: Display name of the repository.
        owner: Repository owner.
        created_at: Repository creation timestamp.
        team_size: Estimated number of active contributors.
        language: Primary programming language.
        events: List of events associated with this project.
    """
    project_id: str
    name: str
    owner: str
    created_at: datetime
    team_size: int = 0
    language: str = "Unknown"
    events: List['Event'] = field(default_factory=list)

    def add_event(self, event: 'Event') -> None:
        """Add an event to the project's timeline."""
        self.events.append(event)

    def get_event_count(self) -> int:
        """Return the total number of events for this project."""
        return len(self.events)

    def get_contributors(self) -> set:
        """Return a set of unique contributor IDs in this project."""
        return {event.author_id for event in self.events if event.author_id}


@dataclass
class Event:
    """
    Represents a single interaction event (issue, PR, comment) in a project.

    Attributes:
        event_id: Unique identifier for the event (e.g., GitHub ID).
        event_type: Type of event (Issue, PR, Comment, etc.).
        project_id: Reference to the parent project.
        author_id: ID of the user who created the event.
        timestamp: When the event occurred.
        parent_event_id: ID of the event this is replying to (if applicable).
        content: Text content of the event (e.g., comment body).
        metadata: Additional raw data from the API.
    """
    event_id: str
    event_type: EventType
    project_id: str
    author_id: str
    timestamp: datetime
    parent_event_id: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_bot(self) -> bool:
        """
        Determine if the author is a bot.
        Checks for '[bot]' suffix or common bot patterns.
        """
        if not self.author_id:
            return False
        return self.author_id.lower().endswith('[bot]') or \
               self.metadata.get('is_bot', False) or \
               self.metadata.get('type') == 'Bot'


@dataclass
class ContributorPair:
    """
    Represents a directed communication link between two contributors.

    Attributes:
        source_id: ID of the initiator (sender).
        target_id: ID of the receiver (recipient).
        project_id: Project where this interaction occurred.
        events: List of events exchanged between this pair.
        mean_delay: Average time (seconds) for target to respond to source.
        response_time_variance: Variance in response times.
    """
    source_id: str
    target_id: str
    project_id: str
    events: List[Event] = field(default_factory=list)
    mean_delay: Optional[float] = None
    response_time_variance: Optional[float] = None

    def add_event(self, event: Event) -> None:
        """Add an event to the interaction history of this pair."""
        self.events.append(event)

    def calculate_delays(self) -> List[float]:
        """
        Calculate inter-arrival times (delays) for this pair.
        Returns a list of delays in seconds.
        """
        if len(self.events) < 2:
            return []

        # Sort events by timestamp to establish sequence
        sorted_events = sorted(self.events, key=lambda e: e.timestamp)
        delays = []

        # Calculate time between consecutive events in the pair
        for i in range(1, len(sorted_events)):
            delta = (sorted_events[i].timestamp - sorted_events[i-1].timestamp).total_seconds()
            if delta > 0:
                delays.append(delta)

        return delays

    def compute_metrics(self) -> None:
        """
        Compute mean_delay and response_time_variance for this pair.
        Updates the object in place.
        """
        delays = self.calculate_delays()
        if not delays:
            self.mean_delay = None
            self.response_time_variance = None
            return

        n = len(delays)
        mean = sum(delays) / n
        variance = sum((d - mean) ** 2 for d in delays) / n if n > 1 else 0.0

        self.mean_delay = mean
        self.response_time_variance = variance


@dataclass
class Metric:
    """
    Represents a derived metric at the project level.

    Attributes:
        project_id: The project this metric belongs to.
        metric_type: Type of metric (e.g., 'mean_delay', 'cohesion_proxy').
        value: The calculated numerical value.
        calculation_timestamp: When the metric was computed.
        metadata: Additional context (e.g., sample size, confidence intervals).
    """
    project_id: str
    metric_type: str
    value: float
    calculation_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary for serialization."""
        return {
            "project_id": self.project_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "calculation_timestamp": self.calculation_timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metric':
        """Create a Metric instance from a dictionary."""
        return cls(
            project_id=data["project_id"],
            metric_type=data["metric_type"],
            value=data["value"],
            calculation_timestamp=datetime.fromisoformat(data["calculation_timestamp"]),
            metadata=data.get("metadata", {})
        )