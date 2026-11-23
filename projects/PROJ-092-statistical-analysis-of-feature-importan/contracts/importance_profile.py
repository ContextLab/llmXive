"""
Importance profile contract definitions.

This module defines the schema for per‑window feature‑importance profiles
produced by the training pipeline.
"""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field, validator


class ImportanceProfile(BaseModel):
    """
    Feature‑importance profile for a single time window.

    Attributes
    ----------
    window_id: Identifier for the window (e.g., integer or string).
    r2_score: R² score of the trained model on this window.
    importance: Mapping from feature name to its permutation‑importance score.
    """

    window_id: str = Field(..., description="Identifier of the processed window.")
    r2_score: float = Field(..., description="R² score of the model on this window.")
    importance: Dict[str, float] = Field(
        ..., description="Feature name → importance score mapping."
    )

    @validator("r2_score")
    def r2_in_range(cls, v: float) -> float:
        """R² must be between 0 and 1 for regression tasks."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("r2_score must be in [0, 1]")
        return v

    @validator("importance")
    def importance_non_negative(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Importance scores should be non‑negative."""
        for feat, imp in v.items():
            if imp < 0:
                raise ValueError(f"Importance for feature '{feat}' is negative")
        return v
