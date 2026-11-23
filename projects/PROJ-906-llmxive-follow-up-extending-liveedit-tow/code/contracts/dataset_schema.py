from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class VideoClipSchema(BaseModel):
    """Pydantic schema for a single video clip metadata record."""
    clip_id: str = Field(..., description="Unique identifier for the clip")
    source_dataset: str = Field(..., description="Source dataset name (e.g., DAVIS, YouTube-VOS)")
    duration_seconds: float = Field(..., gt=0, description="Duration in seconds")
    frame_count: int = Field(..., gt=0, description="Number of frames")
    resolution: tuple = Field(..., description="Resolution as (height, width)")
    fps: float = Field(..., gt=0, description="Frames per second")
    processed_at: Optional[datetime] = Field(default=None, description="Timestamp of processing")
    motion_magnitude: Optional[float] = Field(None, ge=0, description="Mean flow magnitude for stratification")
    stratification_group: Optional[str] = Field(None, description="Assigned motion complexity group")

    @field_validator('resolution')
    @classmethod
    def validate_resolution(cls, v):
        if not isinstance(v, (list, tuple)) or len(v) != 2:
            raise ValueError("Resolution must be a tuple or list of two integers (height, width)")
        if v[0] <= 0 or v[1] <= 0:
            raise ValueError("Resolution dimensions must be positive")
        return tuple(v)


class DatasetSchema(BaseModel):
    """Pydantic schema for a complete dataset record."""
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Human-readable name")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    clips: List[VideoClipSchema] = Field(..., description="List of video clips in the dataset")
    total_clips: int = Field(..., description="Total number of clips")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('total_clips')
    @classmethod
    def validate_total_clips(cls, v, info):
        clips = info.data.get('clips', [])
        if v != len(clips):
            raise ValueError(f"total_clips ({v}) must match number of clips ({len(clips)})")
        return v


class DatasetValidator:
    """
    Validator class to enforce DatasetSchema constraints and validate JSON records.
    """
    @staticmethod
    def validate_from_json(json_str: str) -> DatasetSchema:
        """
        Validates a JSON string against DatasetSchema.
        Raises pydantic.ValidationError on mismatch.
        """
        data = json.loads(json_str)
        return DatasetSchema(**data)

    @staticmethod
    def validate_from_dict(data: Dict[str, Any]) -> DatasetSchema:
        """
        Validates a dictionary against DatasetSchema.
        Raises pydantic.ValidationError on mismatch.
        """
        return DatasetSchema(**data)

    @staticmethod
    def validate_clip_from_json(json_str: str) -> VideoClipSchema:
        """
        Validates a JSON string against VideoClipSchema.
        """
        data = json.loads(json_str)
        return VideoClipSchema(**data)

    @staticmethod
    def validate_clip_from_dict(data: Dict[str, Any]) -> VideoClipSchema:
        """
        Validates a dictionary against VideoClipSchema.
        """
        return VideoClipSchema(**data)
