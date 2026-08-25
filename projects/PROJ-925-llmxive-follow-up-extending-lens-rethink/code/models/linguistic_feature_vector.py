"""
Data Model for Linguistic Feature Vectors.

Defines the structure for extracted features from captions.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import math

class LinguisticFeatureVector(BaseModel):
    """Pydantic model for a linguistic feature vector."""
    caption_id: str
    linguistic_uncertainty_proxy: float = Field(..., description="ln(perplexity)")
    syntactic_depth: int = Field(..., ge=1, description="Depth of dependency tree")
    noun_phrase_density: float = Field(..., ge=0.0, le=1.0)
    token_diversity: float = Field(..., ge=0.0, le=1.0)
    caption_length_tokens: Optional[int] = None
    textual_description_complexity: Optional[int] = None

    @field_validator('linguistic_uncertainty_proxy')
    @classmethod
    def validate_uncertainty(cls, v):
        if math.isnan(v) or math.isinf(v):
            raise ValueError('Linguistic uncertainty proxy cannot be NaN or Inf')
        return v

    @field_validator('noun_phrase_density', 'token_diversity')
    @classmethod
    def validate_ratio(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Ratio values must be between 0 and 1')
        return v
