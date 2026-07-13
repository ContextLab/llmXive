from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json

@dataclass
class DatasetRecord:
    """Represents a single record from a dataset."""
    pre_test_score: float
    post_test_score: float
    instruction_type: str
    covariates: Dict[str, Any] = field(default_factory=dict)
    
    def gain_score(self) -> Optional[float]:
        if self.pre_test_score is not None and self.post_test_score is not None:
            return self.post_test_score - self.pre_test_score
        return None

@dataclass
class SensitivitySweep:
    """Represents a single result from a sensitivity analysis sweep."""
    threshold: float
    t_statistic: float
    p_value: float
    adjusted_alpha: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    power: float
    inference_text: str
    collinearity_diagnostic: Dict[str, Any]
    robustness_warning: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold": self.threshold,
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "adjusted_alpha": self.adjusted_alpha,
            "effect_size": self.effect_size,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "power": self.power,
            "inference_text": self.inference_text,
            "collinearity_diagnostic": self.collinearity_diagnostic,
            "robustness_warning": self.robustness_warning
        }

@dataclass
class AnalysisResult:
    """Aggregates all statistical results for a single analysis run."""
    t_statistic: float
    p_value: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    power: float
    inference_text: str
    collinearity_diagnostic: Dict[str, Any]
    robustness_warning: bool
    sensitivity_sweep: List[SensitivitySweep] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "power": self.power,
            "inference_text": self.inference_text,
            "collinearity_diagnostic": self.collinearity_diagnostic,
            "robustness_warning": self.robustness_warning,
            "sensitivity_sweep": [s.to_dict() for s in self.sensitivity_sweep]
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
