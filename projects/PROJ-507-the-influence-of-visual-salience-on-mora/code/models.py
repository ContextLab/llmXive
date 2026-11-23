"""
Base data models and entities for the Visual Salience Moral Judgments study.

Defines core entities: Scenario, StimulusVariant, Response, and Participant.
Ensures reproducibility by integrating with the seed_everything utility.
"""
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# Import reproducibility utility from existing config module
from config import seed_everything


class AmbiguityLabel(Enum):
    """Labels for scenario ambiguity as per external validation."""
    AMBIGUOUS = "ambiguous"
    CLEAR = "clear"
    UNKNOWN = "unknown"


class SalienceLevel(Enum):
    """Levels of visual salience manipulation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ParticipantStatus(Enum):
    """Status of a participant in the study."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXCLUDED = "excluded"


@dataclass
class Scenario:
    """
    Represents a morally ambiguous scenario (image + context).
    
    Attributes:
        id: Unique identifier for the scenario.
        image_path: Path to the original image file.
        ambiguity_label: Label indicating the ambiguity level (from human coding).
        metadata: Optional dictionary for additional scenario metadata.
    """
    id: str
    image_path: str
    ambiguity_label: AmbiguityLabel = AmbiguityLabel.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure reproducibility if any stochastic operations occur here."""
        # While dataclass init is deterministic, we ensure the global seed is set
        # in case any future extensions or external calls rely on it.
        seed_everything()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scenario to a dictionary for serialization."""
        return {
            "id": self.id,
            "image_path": self.image_path,
            "ambiguity_label": self.ambiguity_label.value,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scenario':
        """Create a Scenario instance from a dictionary."""
        return cls(
            id=data["id"],
            image_path=data["image_path"],
            ambiguity_label=AmbiguityLabel(data["ambiguity_label"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class StimulusVariant:
    """
    Represents a specific visual manipulation of a Scenario.
    
    Attributes:
        id: Unique identifier for the variant.
        scenario_id: Reference to the parent Scenario.
        salience_level: The level of visual salience applied (Low, Med, High).
        image_path: Path to the manipulated image file.
        parameters: Dictionary of parameters used for manipulation (e.g., luminance factor).
    """
    id: str
    scenario_id: str
    salience_level: SalienceLevel
    image_path: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure reproducibility."""
        seed_everything()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stimulus variant to a dictionary."""
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "salience_level": self.salience_level.value,
            "image_path": self.image_path,
            "parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StimulusVariant':
        """Create a StimulusVariant instance from a dictionary."""
        return cls(
            id=data["id"],
            scenario_id=data["scenario_id"],
            salience_level=SalienceLevel(data["salience_level"]),
            image_path=data["image_path"],
            parameters=data.get("parameters", {})
        )


@dataclass
class Response:
    """
    Represents a participant's rating for a specific stimulus variant.
    
    Attributes:
        id: Unique identifier for the response.
        participant_id: Reference to the Participant.
        stimulus_id: Reference to the StimulusVariant.
        rating: The ordinal rating provided (e.g., 1-7 scale).
        timestamp: Time the response was recorded.
        metadata: Optional additional data (e.g., reaction time, device info).
    """
    id: str
    participant_id: str
    stimulus_id: str
    rating: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure reproducibility."""
        seed_everything()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary."""
        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "stimulus_id": self.stimulus_id,
            "rating": self.rating,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Response':
        """Create a Response instance from a dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            id=data["id"],
            participant_id=data["participant_id"],
            stimulus_id=data["stimulus_id"],
            rating=data["rating"],
            timestamp=timestamp or datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class Participant:
    """
    Represents a study participant.
    
    Attributes:
        id: Unique identifier for the participant.
        status: Current status in the study (Pending, Active, Completed, Excluded).
        metadata: Optional demographic or session metadata.
    """
    id: str
    status: ParticipantStatus = ParticipantStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure reproducibility."""
        seed_everything()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the participant to a dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        """Create a Participant instance from a dictionary."""
        return cls(
            id=data["id"],
            status=ParticipantStatus(data["status"]),
            metadata=data.get("metadata", {})
        )

    def update_status(self, new_status: ParticipantStatus) -> None:
        """Update the participant's status."""
        self.status = new_status
        # Ensure reproducibility if status update triggers any stochastic logic
        seed_everything()
