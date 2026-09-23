"""
Data models for the embodied curriculum learning analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json


@dataclass
class DatasetRecord:
    """
    Represents a single record in the dataset.
    """
    pre_test_score: float
    post_test_score: float
    instruction_type: str
    covariates: Dict[str, Any] = field(default_factory=dict)
    record_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pre_test_score": self.pre_test_score,
            "post_test_score": self.post_test_score,
            "instruction_type": self.instruction_type,
            "covariates": self.covariates,
            "record_id": self.record_id
        }


@dataclass
class AnalysisResult:
    """
    Aggregated results from statistical analysis.
    """
    t_test: Optional[Dict[str, Any]] = None
    ancova: Optional[Dict[str, Any]] = None
    effect_size_cohen_d: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    collinearity_diagnostics: Optional[Dict[str, Any]] = None
    achieved_power: Optional[float] = None
    bonferroni_adjusted_p_value: Optional[float] = None
    inference_framing: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "t_test": self.t_test,
            "ancova": self.ancova,
            "effect_size_cohen_d": self.effect_size_cohen_d,
            "confidence_interval": self.confidence_interval,
            "collinearity_diagnostics": self.collinearity_diagnostics,
            "achieved_power": self.achieved_power,
            "bonferroni_adjusted_p_value": self.bonferroni_adjusted_p_value,
            "inference_framing": self.inference_framing
        }


@dataclass
class SensitivitySweep:
    """
    Represents a single point in a sensitivity analysis sweep.
    """
    threshold: float
    effect_size: float
    p_value: float
    sample_size: int
    is_robust: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold": self.threshold,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "sample_size": self.sample_size,
            "is_robust": self.is_robust
        }
