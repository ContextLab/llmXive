"""
Data model for video clips.

Represents a single video unit used in the pretraining pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class VideoClip:
    """
    Represents a video clip with metadata and frame data.

    Attributes:
        id: Unique identifier for the clip. If None, a UUID is generated.
        frames: List of frame data (e.g., file paths, numpy arrays, or byte blobs).
        duration: Duration of the clip in seconds.
        source_url: Original URL or path where the video was sourced from.
    """
    id: str
    frames: List[object]
    duration: float
    source_url: str

    def __post_init__(self):
        """Ensure ID is present."""
        if not self.id:
            raise ValueError("VideoClip ID cannot be empty.")
        if not isinstance(self.frames, list):
            raise TypeError("frames must be a list.")
        if self.duration <= 0:
            raise ValueError("duration must be positive.")

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique ID for a new clip."""
        return str(uuid.uuid4())

    @classmethod
    def from_dict(cls, data: dict) -> "VideoClip":
        """
        Create a VideoClip instance from a dictionary.

        Args:
            data: Dictionary containing clip data.

        Returns:
            VideoClip instance.
        """
        return cls(
            id=data.get("id", cls.generate_id()),
            frames=data.get("frames", []),
            duration=float(data.get("duration", 0.0)),
            source_url=data.get("source_url", ""),
        )

    def to_dict(self) -> dict:
        """
        Convert the VideoClip instance to a dictionary.

        Returns:
            Dictionary representation of the clip.
        """
        return {
            "id": self.id,
            "frames": self.frames,
            "duration": self.duration,
            "source_url": self.source_url,
        }