"""
Data models for the Metaphorical Framing study.
Defines Pydantic models for Participants, Vignettes, and Discourse Posts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, validator


class MetaphorType(str, Enum):
    """Types of metaphorical framing used in the study."""
    BATTLE = "battle"
    JOURNEY = "journey"
    MEDICAL = "medical"


@dataclass
class Participant:
    """
    Represents a study participant.
    Used for both experimental and observational data tracking.
    """
    participant_id: str
    condition: Optional[MetaphorType] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    prior_mental_health_experience: Optional[bool] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Vignette:
    """
    Represents a vignette stimulus.
    Contains the text and the assigned metaphorical framing type.
    """
    vignette_id: str
    metaphor_type: MetaphorType
    text: str
    clinical_details_constant: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class DiscoursePost(BaseModel):
    """
    Represents a single post from a public mental health discourse corpus.
    Used for the observational analysis (User Story 2).
    
    Schema:
    - post_id: Unique identifier for the post
    - text: The full text content of the post
    - author: Author identifier (anonymized)
    - timestamp: ISO formatted timestamp of the post
    - upvotes: Integer count of upvotes/likes
    - comments: Integer count of comments
    - source_subreddit: The source subreddit or forum (optional)
    - raw_data: Dictionary to store any additional metadata from the source
    """
    post_id: str
    text: str
    author: str
    timestamp: datetime
    upvotes: int = 0
    comments: int = 0
    source_subreddit: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            # Handle common ISO formats
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Fallback for timestamp integers (common in Reddit APIs)
                if v.isdigit():
                    return datetime.fromtimestamp(int(v))
                raise ValueError(f"Invalid timestamp format: {v}")
        return v