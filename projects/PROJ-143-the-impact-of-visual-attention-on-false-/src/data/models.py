"""
Base data models for the Visual Attention and False Memory study.

This module defines the core data structures used throughout the pipeline:
- Image: Represents a Visual Genome image with metadata.
- Object: Represents an object instance within an image.
- ParticipantRecall: Represents a participant's recall of objects in an image.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class VerificationStatus(Enum):
    """Enumeration for human verification consensus results."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONSENSUS_REQUIRED = "consensus_required"


@dataclass(frozen=True)
class Image:
    """
    Represents an image from the Visual Genome dataset.

    Attributes:
        image_id (str): Unique identifier for the image (from Visual Genome).
        url (str): Direct URL to the image file.
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        metadata (Dict[str, Any]): Additional metadata (e.g., source, license).
    """
    image_id: str
    url: str
    width: int
    height: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Basic validation
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Image width and height must be positive integers.")


@dataclass(frozen=True)
class Object:
    """
    Represents an object instance within an image.

    Attributes:
        object_id (str): Unique identifier for the object instance.
        image_id (str): Reference to the parent Image.
        label (str): Semantic label of the object (e.g., "dog", "car").
        bbox (Dict[str, int]): Bounding box coordinates: {x, y, width, height}.
        is_false_memory (Optional[bool]): Whether this object was falsely recalled.
        verification_status (VerificationStatus): Status of human consensus verification.
    """
    object_id: str
    image_id: str
    label: str
    bbox: Dict[str, int]
    is_false_memory: Optional[bool] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to a JSON-serializable dictionary."""
        return {
            "object_id": self.object_id,
            "image_id": self.image_id,
            "label": self.label,
            "bbox": self.bbox,
            "is_false_memory": self.is_false_memory,
            "verification_status": self.verification_status.value
        }


@dataclass
class ParticipantRecall:
    """
    Represents a participant's recall transcript for a specific image.

    Attributes:
        participant_id (str): Unique identifier for the participant.
        image_id (str): Reference to the Image being recalled.
        recalled_objects (List[str]): List of object labels recalled by the participant.
        timestamp (str): ISO format timestamp of the recall event.
        session_id (str): Session identifier for grouping multiple recalls.
        metadata (Dict[str, Any]): Additional context (e.g., reaction time, conditions).
    """
    participant_id: str
    image_id: str
    recalled_objects: List[str] = field(default_factory=list)
    timestamp: str = ""
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_recalled_object(self, label: str) -> None:
        """Add an object label to the recall list."""
        if label not in self.recalled_objects:
            self.recalled_objects.append(label)

    def has_recalled(self, label: str) -> bool:
        """Check if a specific label was recalled."""
        return label in self.recalled_objects

    def to_dict(self) -> Dict[str, Any]:
        """Convert recall data to a JSON-serializable dictionary."""
        return {
            "participant_id": self.participant_id,
            "image_id": self.image_id,
            "recalled_objects": self.recalled_objects,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "metadata": self.metadata
        }
