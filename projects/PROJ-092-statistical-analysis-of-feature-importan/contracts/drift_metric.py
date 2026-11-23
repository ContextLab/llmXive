"""
Drift metric contract definitions.

These models capture the output of the pairwise drift analysis between
consecutive windows.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator


class DriftMetric(BaseModel):
    """
    Represents the drift statistics between two consecutive windows.

    Attributes
    ----------
    window_start: Identifier (e.g., integer index) of the earlier window.
    window_end: Identifier of the later window.
    spearman_rho: Spearman rank‑correlation coefficient.
    spearman_p_value: Two‑tailed p‑value associated with the rho.
    high_drift: Boolean flag indicating whether the drift is considered
                significant (based on block‑permutation p‑value < 0.05).
    block_perm_p_value: Optional p‑value from the block permutation test.
    """

    window_start: int = Field(..., description="Index of the earlier window.")
    window_end: int = Field(..., description="Index of the later window.")
    spearman_rho: float = Field(
        ..., description="Spearman rank correlation between feature rankings."
    )
    spearman_p_value: float = Field(
        ..., description="Two‑tailed p‑value for the Spearman rho."
    )
    high_drift: bool = Field(
        ..., description="True if drift is flagged as significant."
    )
    block_perm_p_value: Optional[float] = Field(
        None,
        description=(
            "P‑value from the block permutation significance test. "
            "If None, the test was not performed."
        ),
    )

    @validator("spearman_rho")
    def rho_in_range(cls, v: float) -> float:
        """Spearman rho must be between -1 and 1."""
        if not -1.0 <= v <= 1.0:
            raise ValueError("spearman_rho must be in [-1, 1]")
        return v

    @validator("spearman_p_value", "block_perm_p_value", each_item=True)
    def pvalue_in_range(cls, v: Optional[float]) -> Optional[float]:
        """All p‑values must be in the interval [0, 1]."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("p‑values must be between 0 and 1")
        return v
