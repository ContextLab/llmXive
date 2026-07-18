"""
Data Models for the Embodied Curriculum Learning Analysis Pipeline.

This module defines the core data structures used throughout the pipeline,
including DatasetRecord for input data, AnalysisResult for statistical findings,
and SensitivitySweep for robustness checks.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json


@dataclass
class DatasetRecord:
    """
    Represents a single record in the dataset.

    Attributes:
        id: Unique identifier for the record.
        pre_test_score: Score before intervention (float).
        post_test_score: Score after intervention (float).
        instruction_type: Type of instruction (e.g., 'embodied', 'static').
        covariates: Additional covariates as a dictionary.
        gain_score: Calculated gain (post - pre), computed during processing.
    """
    id: str
    pre_test_score: Optional[float] = None
    post_test_score: Optional[float] = None
    instruction_type: Optional[str] = None
    covariates: Dict[str, Any] = field(default_factory=dict)
    gain_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the record to a dictionary.

        Returns:
            Dictionary representation of the record.
        """
        return {
            "id": self.id,
            "pre_test_score": self.pre_test_score,
            "post_test_score": self.post_test_score,
            "instruction_type": self.instruction_type,
            "covariates": self.covariates,
            "gain_score": self.gain_score
        }

@dataclass
class AnalysisResult:
    """
    Represents the result of a statistical analysis.

    Attributes:
        concept_name: Name of the concept being analyzed.
        t_statistic: The calculated t-statistic.
        p_value: The calculated p-value.
        effect_size: Cohen's d effect size.
        confidence_interval: Tuple of (lower, upper) for the confidence interval.
        bonferroni_adjusted_p: Bonferroni-corrected p-value.
        is_significant: Boolean indicating significance after correction.
        power: Achieved statistical power.
        underpowered: Boolean indicating if power < 0.80.
        collinearity_detected: Boolean indicating if collinearity was detected.
        associational_framing: String framing the results as associational.
    """
    concept_name: str
    t_statistic: float
    p_value: float
    effect_size: float
    confidence_interval: tuple
    bonferroni_adjusted_p: float
    is_significant: bool
    power: float
    underpowered: bool
    collinearity_detected: bool
    associational_framing: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "concept_name": self.concept_name,
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "bonferroni_adjusted_p": self.bonferroni_adjusted_p,
            "is_significant": self.is_significant,
            "power": self.power,
            "underpowered": self.underpowered,
            "collinearity_detected": self.collinearity_detected,
            "associational_framing": self.associational_framing
        }

@dataclass
class SensitivitySweep:
    """
    Represents the result of a sensitivity analysis sweep.

    Attributes:
        threshold: The threshold value used for this sweep.
        effect_size: Effect size calculated at this threshold.
        is_significant: Boolean indicating significance at this threshold.
        sample_size: Number of samples used in this sweep.
    """
    threshold: float
    effect_size: float
    is_significant: bool
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sweep result to a dictionary.

        Returns:
            Dictionary representation of the sweep result.
        """
        return {
            "threshold": self.threshold,
            "effect_size": self.effect_size,
            "is_significant": self.is_significant,
            "sample_size": self.sample_size
        }