"""
Base data models for the Visual Attention and False Memory study.

Defines the core data structures for Image, Object, and ParticipantRecall
entities used throughout the pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass(frozen=True)
class Image:
    """
    Represents a single image from the Visual Genome dataset.
    
    Attributes:
        image_id: Unique identifier for the image in Visual Genome.
        filename: Local filename of the downloaded image.
        width: Width of the image in pixels.
        height: Height of the image in pixels.
        url: Original URL of the image (optional).
        metadata: Additional metadata dictionary from the dataset.
    """
    image_id: int
    filename: str
    width: int
    height: int
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_aspect_ratio(self) -> float:
        """Calculate the aspect ratio (width / height)."""
        if self.height == 0:
            return 0.0
        return self.width / self.height
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "image_id": self.image_id,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "url": self.url,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Image":
        """Create an Image instance from a dictionary."""
        return cls(
            image_id=data["image_id"],
            filename=data["filename"],
            width=data["width"],
            height=data["height"],
            url=data.get("url"),
            metadata=data.get("metadata", {})
        )


@dataclass(frozen=True)
class Object:
    """
    Represents an annotated object within an image from Visual Genome.
    
    Attributes:
        object_id: Unique identifier for the object annotation.
        image_id: The ID of the parent image.
        name: The label/name of the object (e.g., "dog", "car").
        x: X-coordinate of the bounding box top-left corner.
        y: Y-coordinate of the bounding box top-left corner.
        w: Width of the bounding box.
        h: Height of the bounding box.
        attributes: List of attribute strings for the object.
        is_visible: Boolean indicating if the object is visible.
    """
    object_id: int
    image_id: int
    name: str
    x: int
    y: int
    w: int
    h: int
    attributes: List[str] = field(default_factory=list)
    is_visible: bool = True
    
    @property
    def area(self) -> int:
        """Calculate the area of the bounding box."""
        return self.w * self.h
    
    @property
    def center_x(self) -> float:
        """Calculate the center X coordinate."""
        return self.x + (self.w / 2)
    
    @property
    def center_y(self) -> float:
        """Calculate the center Y coordinate."""
        return self.y + (self.h / 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "object_id": self.object_id,
            "image_id": self.image_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "attributes": self.attributes,
            "is_visible": self.is_visible
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Object":
        """Create an Object instance from a dictionary."""
        return cls(
            object_id=data["object_id"],
            image_id=data["image_id"],
            name=data["name"],
            x=data["x"],
            y=data["y"],
            w=data["w"],
            h=data["h"],
            attributes=data.get("attributes", []),
            is_visible=data.get("is_visible", True)
        )


@dataclass(frozen=True)
class ParticipantRecall:
    """
    Represents a participant's recall of an image.
    
    This model captures the transcript of what a participant remembered
    seeing in an image, which is compared against the actual image content
    to identify false memories.
    
    Attributes:
        recall_id: Unique identifier for this recall instance.
        participant_id: Identifier for the participant.
        image_id: The ID of the image being recalled (from Visual Genome).
        transcript: The full text transcript of what the participant recalled.
        timestamp: When the recall was recorded.
        recalled_objects: List of objects mentioned in the transcript.
        is_false_memory: Boolean flag indicating if this is a false memory
                        (object recalled but not present in the image).
        false_memory_objects: List of object names that were falsely recalled.
        metadata: Additional metadata about the recall session.
    """
    recall_id: str
    participant_id: str
    image_id: int
    transcript: str
    timestamp: datetime
    recalled_objects: List[str] = field(default_factory=list)
    is_false_memory: bool = False
    false_memory_objects: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_word_count(self) -> int:
        """Calculate the number of words in the transcript."""
        return len(self.transcript.split())
    
    def get_object_count(self) -> int:
        """Calculate the number of objects mentioned in the recall."""
        return len(self.recalled_objects)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "recall_id": self.recall_id,
            "participant_id": self.participant_id,
            "image_id": self.image_id,
            "transcript": self.transcript,
            "timestamp": self.timestamp.isoformat(),
            "recalled_objects": self.recalled_objects,
            "is_false_memory": self.is_false_memory,
            "false_memory_objects": self.false_memory_objects,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParticipantRecall":
        """Create a ParticipantRecall instance from a dictionary."""
        # Handle timestamp parsing
        timestamp_str = data.get("timestamp")
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str)
        elif isinstance(timestamp_str, datetime):
            timestamp = timestamp_str
        else:
            timestamp = datetime.now()
        
        return cls(
            recall_id=data["recall_id"],
            participant_id=data["participant_id"],
            image_id=data["image_id"],
            transcript=data["transcript"],
            timestamp=timestamp,
            recalled_objects=data.get("recalled_objects", []),
            is_false_memory=data.get("is_false_memory", False),
            false_memory_objects=data.get("false_memory_objects", []),
            metadata=data.get("metadata", {})
        )