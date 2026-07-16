"""
Data model for a raw caption record from the Pick-a-Pic dataset.

This class represents a single row from the source data after initial
filtering (non-empty captions, valid image paths).
"""
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CaptionRecord(BaseModel):
    """
    Represents a single caption record with its associated metadata.

    Attributes:
        record_id: Unique identifier for the record (usually from dataset index).
        caption: The text caption associated with the image.
        image_path: Local or remote path to the image file.
        prompt_id: The original prompt ID from the dataset (if available).
        winner_id: ID of the 'winner' image in the pair (if applicable).
        loser_id: ID of the 'loser' image in the pair (if applicable).
        raw_metadata: Dictionary to store any additional raw fields not explicitly mapped.
    """
    record_id: str = Field(..., description="Unique identifier for the record")
    caption: str = Field(..., min_length=1, description="The text caption")
    image_path: str = Field(..., description="Path to the image file")
    prompt_id: Optional[str] = Field(None, description="Original prompt ID")
    winner_id: Optional[str] = Field(None, description="Winner image ID")
    loser_id: Optional[str] = Field(None, description="Loser image ID")
    raw_metadata: Optional[dict] = Field(default_factory=dict, description="Additional raw fields")

    @field_validator('caption')
    @classmethod
    def caption_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Caption cannot be empty or whitespace")
        return v.strip()

    @property
    def is_pair(self) -> bool:
        """Returns True if this record represents a winner/loser pair."""
        return self.winner_id is not None and self.loser_id is not None
