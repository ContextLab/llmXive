from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json


@dataclass
class DatasetRecord:
    """
    Represents a single record in the dataset.
    
    Attributes:
        pre_test_score: Score before instruction.
        post_test_score: Score after instruction.
        instruction_type: Type of instruction received (e.g., 'embodied', 'static').
        covariates: Additional static data structure for covariates.
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetRecord':
        """Create a record from a dictionary."""
        return cls(
            pre_test_score=data["pre_test_score"],
            post_test_score=data["post_test_score"],
            instruction_type=data["instruction_type"],
            covariates=data.get("covariates", {})
        )


@dataclass
class AnalysisResult:
    """
    Represents the result of a statistical analysis.
    
    Attributes:
        t_statistic: The calculated t-statistic.
        p_value: The calculated p-value.
        effect_size: The calculated effect size (e.g., Cohen's d).
        confidence_interval: The confidence interval for the effect size.
        method: The statistical method used.
        associational_framing: Flag indicating if results are framed as associational.
        power: The achieved statistical power.
        collinearity_diagnostic: Diagnostic info regarding collinearity.
        robustness_warning: Flag indicating if robustness warnings exist.
    """
    t_statistic: float
    p_value: float
    effect_size: float
    confidence_interval: List[float]
    method: str
    associational_framing: bool = True
    power: Optional[float] = None
    collinearity_diagnostic: Optional[Dict[str, Any]] = None
    robustness_warning: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "method": self.method,
            "associational_framing": self.associational_framing,
            "power": self.power,
            "collinearity_diagnostic": self.collinearity_diagnostic,
            "robustness_warning": self.robustness_warning
        }


@dataclass
class SensitivitySweep:
    """
    Represents a single entry in a sensitivity sweep analysis.
    
    Attributes:
        threshold: The significance threshold used.
        effect_size: The effect size calculated at this threshold.
        significant: Whether the result was significant at this threshold.
    """
    threshold: float
    effect_size: float
    significant: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sweep entry to a dictionary."""
        return {
            "threshold": self.threshold,
            "effect_size": self.effect_size,
            "significant": self.significant
        }
