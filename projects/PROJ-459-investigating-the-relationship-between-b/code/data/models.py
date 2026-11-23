"""
Pydantic data models for the brain‑network‑music‑preference pipeline.

These models provide a typed schema for the core entities exchanged
between the various pipeline stages:

* ``Subject`` – participant identifier and their genre preference scores.
* ``TimeSeries`` – a single ROI's BOLD time‑course.
* ``NetworkMetric`` – a computed graph‑theoretic metric for a subject.
* ``CorrelationResult`` – the statistical association between a metric and a genre.
* ``SensitivityReport`` – stability information from the sliding‑window sensitivity analysis.

The models include lightweight validation to catch obvious data‑integrity
problems early (e.g., malformed subject IDs, empty score dictionaries,
out‑of‑range p‑values). They are deliberately minimal – the heavy‑weight
statistical and neuro‑imaging logic lives elsewhere in the code base.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Subject(BaseModel):
    """
    Represents an individual participant.

    Attributes
    ----------
    id :
        BIDS‑style subject identifier (e.g., ``sub-01``).  The validator
        enforces the ``sub-`` prefix followed by at least one digit.
    genre_scores :
        Mapping from genre name to a numeric preference score.
        Scores are expected to be finite numbers; empty dictionaries are
        rejected because downstream analyses require at least one genre.
    """

    id: str = Field(..., description="BIDS‑style subject identifier, e.g. 'sub-01'")
    genre_scores: Dict[str, float] = Field(
        ..., description="Dictionary of genre → preference score"
    )

    @validator("id")
    def _validate_id(cls, v: str) -> str:
        if not v.startswith("sub-") or not v[4:].isdigit():
            raise ValueError(
                f"Subject id '{v}' must start with 'sub-' followed by digits"
            )
        return v

    @validator("genre_scores")
    def _validate_genre_scores(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("genre_scores must contain at least one entry")
        for genre, score in v.items():
            if not isinstance(score, (int, float)):
                raise TypeError(f"Score for genre '{genre}' must be numeric")
            if not (float("-inf") < float(score) < float("inf")):
                raise ValueError(f"Score for genre '{genre}' must be a finite number")
        return v


class TimeSeries(BaseModel):
    """
    BOLD time‑course for a single ROI.

    Attributes
    ----------
    roi_id :
        Identifier of the ROI (e.g., ``Schaefer400_1``).  No strict format
        is enforced – the downstream atlas loader provides the canonical
        naming scheme.
    values :
        List of signal amplitudes sampled at each TR.  The list must be
        non‑empty; zero‑length series are indicative of a processing error.
    """

    roi_id: str = Field(..., description="ROI identifier")
    values: List[float] = Field(..., description="Time‑series values for the ROI")

    @validator("values")
    def _non_empty(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("TimeSeries.values must contain at least one sample")
        return v


class NetworkMetric(BaseModel):
    """
    A graph‑theoretic metric derived from a subject's functional connectivity.

    Attributes
    ----------
    subject_id :
        BIDS‑style identifier linking the metric back to a participant.
    metric_name :
        Human‑readable name (e.g., ``global_efficiency``).
    value :
        Numeric result of the metric calculation.
    """

    subject_id: str = Field(..., description="Subject identifier (BIDS style)")
    metric_name: str = Field(..., description="Name of the network metric")
    value: float = Field(..., description="Computed metric value")

    @validator("subject_id")
    def _validate_subject_id(cls, v: str) -> str:
        if not v.startswith("sub-") or not v[4:].isdigit():
            raise ValueError(
                f"subject_id '{v}' must start with 'sub-' followed by digits"
            )
        return v

    @validator("metric_name")
    def _non_empty_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("metric_name cannot be empty")
        return v


class CorrelationResult(BaseModel):
    """
    Result of a Spearman correlation between a network metric and a genre score.

    Attributes
    ----------
    metric :
        Name of the network metric (matches ``NetworkMetric.metric_name``).
    genre :
        Name of the genre column used in the behavioural data.
    r :
        Spearman correlation coefficient (range -1 → 1).
    p_raw :
        Two‑tailed raw p‑value.
    p_adj :
        Benjamini‑Hochberg adjusted p‑value (0 → 1).
    """

    metric: str = Field(..., description="Metric name")
    genre: str = Field(..., description="Genre name")
    r: float = Field(..., description="Spearman correlation coefficient")
    p_raw: float = Field(..., description="Raw p‑value")
    p_adj: float = Field(..., description="BH‑adjusted p‑value")

    @validator("r")
    def _r_range(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise ValueError("Correlation coefficient r must be between -1 and 1")
        return v

    @validator("p_raw", "p_adj")
    def _p_range(cls, v: float, field) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"{field.name} must be between 0 and 1")
        return v


class SensitivityReport(BaseModel):
    """
    Summary of the sliding‑window sensitivity analysis.

    Attributes
    ----------
    window_size :
        Window length (in TRs) that was evaluated.
    icc :
        Intraclass Correlation Coefficient across the tested window sizes
        for a given metric (0 → 1).  Values below 0.7 are typically regarded
        as insufficiently stable.
    """

    window_size: int = Field(..., description="Sliding‑window length in TRs")
    icc: float = Field(..., description="Intraclass correlation coefficient")

    @validator("window_size")
    def _positive_window(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("window_size must be a positive integer")
        return v

    @validator("icc")
    def _icc_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("icc must be between 0 and 1")
        return v

# Export names for ``from data.models import …`` convenience
__all__ = [
    "Subject",
    "TimeSeries",
    "NetworkMetric",
    "CorrelationResult",
    "SensitivityReport",
]