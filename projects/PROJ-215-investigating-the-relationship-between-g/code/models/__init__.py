"""
Data model definitions for the Gut Microbiome – Mental Health study.

This module provides the core dataclasses used throughout the pipeline:
- MicrobiomeSample
- MentalHealthRecord
- AssociationResult

The classes are deliberately lightweight and contain only the attributes
required by the downstream analysis scripts. They are exported via
``__all__`` for convenient import:

    from code.models import MicrobiomeSample, MentalHealthRecord, AssociationResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Type alias for counts (sparse or dense representation handled by implementation)
Counts = Union[Dict[str, int], np.ndarray, List[int]]

__all__ = [
    "MicrobiomeSample",
    "MentalHealthRecord",
    "AssociationResult",
]


@dataclass
class MicrobiomeSample:
    """
    Represents a single microbiome sample.

    Attributes
    ----------
    sample_id: str
        Unique identifier for the sample (e.g., from AGP).
    counts: Counts
        Taxonomic abundance counts. Can be a dict ``{taxon: count}``,
        a NumPy array, or a list of integers.
    metadata: Dict[str, Any]
        Dictionary of sample‑level metadata (e.g., sequencing depth,
        collection date, location). Defaults to an empty dict.
    """
    sample_id: str
    counts: Counts
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate basic structure."""
        if not self.sample_id:
            raise ValueError("sample_id cannot be empty")
        if self.counts is None:
            raise ValueError("counts cannot be None")


@dataclass
class MentalHealthRecord:
    """
    Represents mental health assessment data for a subject.

    Attributes
    ----------
    phq9: Optional[float]
        Patient Health Questionnaire‑9 score (0‑27).
    gad7: Optional[float]
        Generalized Anxiety Disorder‑7 score (0‑21).
    age: Optional[float]
        Age of the subject in years.
    bmi: Optional[float]
        Body Mass Index.
    subject_id: Optional[str]
        Unique identifier linking to microbiome samples.
    """
    phq9: Optional[float] = None
    gad7: Optional[float] = None
    age: Optional[float] = None
    bmi: Optional[float] = None
    subject_id: Optional[str] = None

    def has_missing_key_values(self) -> bool:
        """Check if any critical outcome or covariate is missing."""
        return any(v is None for v in [self.phq9, self.gad7, self.age, self.bmi])

    def is_high_depression(self) -> bool:
        """PHQ‑9 ≥ 10 indicates moderate‑to‑severe depression."""
        if self.phq9 is None:
            return False
        return self.phq9 >= 10

    def is_high_anxiety(self) -> bool:
        """GAD‑7 ≥ 10 indicates moderate‑to‑severe anxiety."""
        if self.gad7 is None:
            return False
        return self.gad7 >= 10


@dataclass
class AssociationResult:
    """
    Represents the result of a statistical association test between a taxon
    (or diversity metric) and a mental‑health outcome.

    Attributes
    ----------
    taxon: str
        Taxonomic identifier or name.
    coef: float
        Correlation coefficient (e.g., Spearman rho).
    pval: float
        Unadjusted p‑value.
    qval: float
        Adjusted p‑value (e.g., Benjamini‑Hochberg).
    direction: str
        ``'positive'`` or ``'negative'`` – derived from ``coef``.
    metric: str
        Optional context for which outcome was tested
        (e.g., ``'PHQ9'``, ``'GAD7'``, ``'Shannon'``).
    """
    taxon: str
    coef: float
    pval: float
    qval: float
    direction: str = ""
    metric: str = ""

    def __post_init__(self) -> None:
        """Derive the ``direction`` attribute from the coefficient."""
        if self.coef < 0:
            self.direction = "negative"
        elif self.coef > 0:
            self.direction = "positive"
        else:
            self.direction = "neutral"

    def is_significant(self, threshold: float = 0.05) -> bool:
        """Return ``True`` if the adjusted p‑value is below ``threshold``."""
        return self.qval < threshold