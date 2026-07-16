"""
Data model for the linguistic feature vector extracted from a caption.

This class represents the output of the feature extraction pipeline (US1),
containing semantic entropy, syntactic depth, noun-phrase density, and token diversity.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import math


class LinguisticFeatureVector(BaseModel):
    """
    Represents the computed linguistic features for a single caption.

    Attributes:
        record_id: Reference to the original CaptionRecord ID.
        semantic_entropy: Calculated as ln(perplexity) from BERT.
        syntactic_depth: Maximum depth of the dependency tree (spaCy).
        noun_phrase_density: Ratio of noun phrases to total tokens.
        token_diversity: Type-token ratio (unique tokens / total tokens).
        feature_version: Version string of the feature extraction logic.
    """
    record_id: str = Field(..., description="Reference to the original CaptionRecord ID")
    semantic_entropy: float = Field(..., ge=0.0, description="ln(perplexity) from BERT model")
    syntactic_depth: int = Field(..., ge=0, description="Maximum dependency tree depth")
    noun_phrase_density: float = Field(..., ge=0.0, le=1.0, description="Ratio of NPs to total tokens")
    token_diversity: float = Field(..., ge=0.0, le=1.0, description="Type-token ratio")
    feature_version: str = Field("1.0.0", description="Version of the feature extraction logic")

    @field_validator('semantic_entropy')
    @classmethod
    def validate_entropy(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Semantic entropy cannot be NaN or Inf")
        return v

    @field_validator('noun_phrase_density', 'token_diversity')
    @classmethod
    def validate_ratio(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"Ratio cannot be NaN or Inf")
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Ratio must be between 0.0 and 1.0, got {v}")
        return v

    def to_dict(self) -> dict:
        """Convert the feature vector to a dictionary for serialization."""
        return self.model_dump()
