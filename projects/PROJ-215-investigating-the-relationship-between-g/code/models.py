"""
Base data models and entities for the Gut Microbiome - Mental Health study.

This module defines the core data structures used throughout the pipeline:
- MicrobiomeSample: Represents a single sample with OTU/ASV counts and metadata.
- MentalHealthRecord: Represents clinical/psychological survey data for a subject.
- AssociationResult: Represents the output of statistical association tests.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import numpy as np

# Type alias for counts (sparse or dense representation handled by implementation)
Counts = Union[Dict[str, int], np.ndarray, List[int]]


@dataclass
class MicrobiomeSample:
    """
    Represents a single microbiome sample.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., from AGP).
        counts: Taxonomic abundance counts. Can be a dict {taxon: count},
                a numpy array, or a list.
        metadata: Dictionary of sample-level metadata (e.g., sequencing_depth,
                  collection_date, location).
    """
    sample_id: str
    counts: Counts
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate basic structure."""
        if not self.sample_id:
            raise ValueError("sample_id cannot be empty")
        if self.counts is None:
            raise ValueError("counts cannot be None")


@dataclass
class MentalHealthRecord:
    """
    Represents mental health assessment data for a subject.

    Attributes:
        phq9: Patient Health Questionnaire-9 score (0-27).
        gad7: Generalized Anxiety Disorder-7 score (0-21).
        age: Age of the subject in years.
        bmi: Body Mass Index.
        subject_id: Unique identifier linking to microbiome samples.
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
        """PHQ-9 >= 10 indicates moderate-to-severe depression."""
        if self.phq9 is None:
            return False
        return self.phq9 >= 10

    def is_high_anxiety(self) -> bool:
        """GAD-7 >= 10 indicates moderate-to-severe anxiety."""
        if self.gad7 is None:
            return False
        return self.gad7 >= 10


@dataclass
class AssociationResult:
    """
    Represents the result of a statistical association test between a taxon
    and a mental health metric.

    Attributes:
        taxon: The taxonomic identifier or name.
        coef: The correlation coefficient (e.g., Spearman rho).
        pval: The unadjusted p-value.
        qval: The adjusted p-value (e.g., Benjamini-Hochberg).
        direction: String indicating the direction of association ('positive' or 'negative').
        metric: The mental health metric tested (e.g., 'PHQ9', 'GAD7', 'Shannon').
    """
    taxon: str
    coef: float
    pval: float
    qval: float
    direction: str  # 'positive' or 'negative'
    metric: str = ""  # Optional context for which outcome was tested

    def __post_init__(self):
        if self.coef < 0:
            self.direction = "negative"
        elif self.coef > 0:
            self.direction = "positive"
        else:
            self.direction = "neutral"

    def is_significant(self, threshold: float = 0.05) -> bool:
        """Check if the result is significant after adjustment."""
        return self.qval < threshold
