from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json

@dataclass
class DatasetRecord:
    """
    Represents a single data point for analysis.
    """
    pre_test_score: float
    post_test_score: float
    instruction_type: Optional[str]  # Can be 'embodied', 'static', or None
    covariates: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure instruction_type is a string or None
        if self.instruction_type is not None and not isinstance(self.instruction_type, str):
            self.instruction_type = str(self.instruction_type)

@dataclass
class AnalysisResult:
    """
    Aggregates results from statistical tests.
    """
    test_type: str  # e.g., "Welch's t-test", "Student's t-test"
    statistic: float
    p_value: float
    effect_size: float  # Cohen's d
    confidence_interval: tuple
    sample_sizes: Dict[str, int]  # e.g., {"embodied": 50, "static": 50}
    power: float
    robustness_warning: bool = False
    associational_framing: str = "Associational only. No causal claims."
    collinearity_diagnostics: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "sample_sizes": self.sample_sizes,
            "power": self.power,
            "robustness_warning": self.robustness_warning,
            "associational_framing": self.associational_framing,
            "collinearity_diagnostics": self.collinearity_diagnostics
        }

@dataclass
class SensitivitySweep:
    """
    Represents results from a sensitivity analysis sweep.
    """
    thresholds: List[float]
    effect_sizes: List[float]
    p_values: List[float]
    robustness_warning: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thresholds": self.thresholds,
            "effect_sizes": self.effect_sizes,
            "p_values": self.p_values,
            "robustness_warning": self.robustness_warning
        }
