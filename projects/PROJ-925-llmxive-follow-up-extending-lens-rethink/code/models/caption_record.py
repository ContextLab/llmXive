"""
Data Model for Caption Records.

Defines the structure for individual caption entries.
"""
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field, field_validator

@dataclass
class CaptionRecord:
    """Simple dataclass for a caption record."""
    caption_id: str
    caption: str
    image_path: Optional[str] = None
    human_rating: Optional[float] = None
    clip_score: Optional[float] = None

class CaptionRecordModel(BaseModel):
    """Pydantic model for validation of caption records."""
    caption_id: str
    caption: str
    image_path: Optional[str] = None
    human_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    clip_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('caption')
    @classmethod
    def caption_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Caption cannot be empty')
        return v.strip()
