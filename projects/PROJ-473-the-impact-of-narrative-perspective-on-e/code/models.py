"""
Base data models for the Narrative Perspective Impact study.

Defines the core data structures for StoryDocument and ReaderResponse
as required by the project specification.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class StoryDocument:
    """
    Represents a single story document with its metadata and extracted features.

    Attributes:
        story_id: Unique identifier for the story (e.g., from Gutenberg or OSF).
        title: Title of the story.
        author: Author of the story.
        source: Origin of the text (e.g., 'gutenberg', 'osf', 'custom').
        text: The full raw text content of the story.
        language: Detected language code (e.g., 'en').
        word_count: Total number of words in the text.
        perspective_features: Dictionary of extracted perspective metrics.
            Expected keys: 'pronoun_density_1st', 'pronoun_density_2nd',
            'pronoun_density_3rd', 'narrator_distance_score'.
        created_at: Timestamp when this record was created.
    """
    story_id: str
    title: str
    author: str
    source: str
    text: str
    language: str = "en"
    word_count: int = 0
    perspective_features: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate word count if text is provided and count is missing."""
        if self.text and self.word_count == 0:
            self.word_count = len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "story_id": self.story_id,
            "title": self.title,
            "author": self.author,
            "source": self.source,
            "text": self.text,
            "language": self.language,
            "word_count": self.word_count,
            "perspective_features": self.perspective_features,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryDocument":
        """Create a StoryDocument from a dictionary."""
        # Handle datetime parsing if it exists as a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            story_id=data["story_id"],
            title=data["title"],
            author=data["author"],
            source=data["source"],
            text=data["text"],
            language=data.get("language", "en"),
            word_count=data.get("word_count", 0),
            perspective_features=data.get("perspective_features", {}),
            created_at=created_at or datetime.now(),
        )


@dataclass
class ReaderResponse:
    """
    Represents a single reader's response to a story.

    Attributes:
        response_id: Unique identifier for this response record.
        story_id: Foreign key linking to the StoryDocument.
        participant_id: Anonymized identifier for the participant.
        empathy_score: Aggregated score from the Interpersonal Reactivity Index (IRI).
        moral_judgement_score: Score representing deontological vs consequentialist leaning.
        demographic_data: Optional dictionary of demographic info (age, gender, culture, etc.).
        attention_check_passed: Boolean indicating if the participant passed attention checks.
        response_time_seconds: Time taken to complete the response.
        raw_responses: Dictionary of raw item-level scores before aggregation.
        created_at: Timestamp when this record was created.
    """
    response_id: str
    story_id: str
    participant_id: str
    empathy_score: Optional[float] = None
    moral_judgement_score: Optional[float] = None
    demographic_data: Dict[str, Any] = field(default_factory=dict)
    attention_check_passed: bool = True
    response_time_seconds: Optional[float] = None
    raw_responses: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def is_valid(self) -> bool:
        """
        Check if the response is valid for analysis.

        Returns True if attention checks passed and core scores are present.
        """
        if not self.attention_check_passed:
            return False
        if self.empathy_score is None or self.moral_judgement_score is None:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "response_id": self.response_id,
            "story_id": self.story_id,
            "participant_id": self.participant_id,
            "empathy_score": self.empathy_score,
            "moral_judgement_score": self.moral_judgement_score,
            "demographic_data": self.demographic_data,
            "attention_check_passed": self.attention_check_passed,
            "response_time_seconds": self.response_time_seconds,
            "raw_responses": self.raw_responses,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReaderResponse":
        """Create a ReaderResponse from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            response_id=data["response_id"],
            story_id=data["story_id"],
            participant_id=data["participant_id"],
            empathy_score=data.get("empathy_score"),
            moral_judgement_score=data.get("moral_judgement_score"),
            demographic_data=data.get("demographic_data", {}),
            attention_check_passed=data.get("attention_check_passed", True),
            response_time_seconds=data.get("response_time_seconds"),
            raw_responses=data.get("raw_responses", {}),
            created_at=created_at or datetime.now(),
        )