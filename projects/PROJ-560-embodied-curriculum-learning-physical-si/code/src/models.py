from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json


@dataclass
class DatasetRecord:
    """
    Represents a single data record for analysis.

    Attributes:
        pre_test_score (float): Score before the intervention.
        post_test_score (float): Score after the intervention.
        instruction_type (str): Type of instruction received (e.g., 'embodied', 'static').
        covariates (Dict[str, Any]): Additional static data fields.
    """
    pre_test_score: float
    post_test_score: float
    instruction_type: str
    covariates: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "pre_test_score": self.pre_test_score,
            "post_test_score": self.post_test_score,
            "instruction_type": self.instruction_type,
            "covariates": self.covariates
        }


@dataclass
class AnalysisResult:
    """
    Aggregates the results of a statistical analysis.

    Attributes:
        t_statistic (float): The calculated t-statistic.
        p_value (float): The calculated p-value.
        effect_size (float): Cohen's d effect size.
        confidence_interval (Optional[Tuple[float, float]]): 95% confidence interval.
        methodological_caveats (List[str]): List of framing caveats (e.g., "associational").
        power (Optional[float]): Achieved statistical power.
        collinearity_report (Optional[Dict[str, Any]]): Collinearity diagnostics.
        robustness_warning (Optional[bool]): Flag indicating if robustness checks failed.
    """
    t_statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Optional[tuple] = None
    methodological_caveats: List[str] = field(default_factory=list)
    power: Optional[float] = None
    collinearity_report: Optional[Dict[str, Any]] = None
    robustness_warning: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for JSON serialization."""
        return {
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            "methodological_caveats": self.methodological_caveats,
            "power": self.power,
            "collinearity_report": self.collinearity_report,
            "robustness_warning": self.robustness_warning
        }


@dataclass
class SensitivitySweep:
    """
    Represents the results of a sensitivity analysis sweep.

    Attributes:
        threshold (float): The threshold value used for this sweep point.
        effect_size (float): The calculated effect size at this threshold.
        p_value (float): The calculated p-value at this threshold.
        sample_size (int): The number of samples used in this sweep point.
    """
    threshold: float
    effect_size: float
    p_value: float
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sweep result to a dictionary."""
        return {
            "threshold": self.threshold,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "sample_size": self.sample_size
        }
