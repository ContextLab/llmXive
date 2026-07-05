"""
Result data structures for statistical analysis.

This module defines dataclasses for storing and serializing
statistical model results, including coefficients, confidence intervals,
and p-values.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import numpy as np


class ModelType(Enum):
    """Enumeration of model types supported by the pipeline."""
    LMM = "LinearMixedModel"
    OLS = "OrdinaryLeastSquares"
    RATIO = "RatioAnalysis"


@dataclass
class StatisticalModel:
    """
    Data class representing a fitted statistical model.

    Attributes:
        subfield: The hippocampal subfield analyzed.
        formula: The model formula used.
        beta_ace: The beta coefficient for ACE score.
        ci_95_low: Lower bound of 95% confidence interval.
        ci_95_high: Upper bound of 95% confidence interval.
        p_value: Uncorrected p-value.
        log_likelihood: Model log-likelihood.
        aic: Akaike Information Criterion.
        bic: Bayesian Information Criterion.
        n_obs: Number of observations.
    """
    subfield: str
    formula: str
    beta_ace: float
    ci_95_low: float
    ci_95_high: float
    p_value: float
    log_likelihood: float
    aic: float
    bic: float
    n_obs: int
    corrected_p_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model results to a dictionary."""
        return {
            "subfield": self.subfield,
            "formula": self.formula,
            "beta_ace": self.beta_ace,
            "ci_95_low": self.ci_95_low,
            "ci_95_high": self.ci_95_high,
            "p_value": self.p_value,
            "corrected_p_value": self.corrected_p_value,
            "log_likelihood": self.log_likelihood,
            "aic": self.aic,
            "bic": self.bic,
            "n_obs": self.n_obs
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatisticalModel":
        """Create a StatisticalModel from a dictionary."""
        return cls(
            subfield=data["subfield"],
            formula=data["formula"],
            beta_ace=data["beta_ace"],
            ci_95_low=data["ci_95_low"],
            ci_95_high=data["ci_95_high"],
            p_value=data["p_value"],
            log_likelihood=data["log_likelihood"],
            aic=data["aic"],
            bic=data["bic"],
            n_obs=data["n_obs"],
            corrected_p_value=data.get("corrected_p_value")
        )


@dataclass
class AnalysisResult:
    """
    Container for the full analysis results.

    Attributes:
        models: List of StatisticalModel objects.
        sensitivity_analysis: Optional sensitivity analysis results.
        robustness_metrics: Optional robustness metrics.
    """
    models: List[StatisticalModel] = field(default_factory=list)
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    robustness_metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to a dictionary."""
        return {
            "models": [m.to_dict() for m in self.models],
            "sensitivity_analysis": self.sensitivity_analysis,
            "robustness_metrics": self.robustness_metrics
        }

    def save_json(self, filepath: str) -> None:
        """Save results to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, filepath: str) -> "AnalysisResult":
        """Load results from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        models = [StatisticalModel.from_dict(m) for m in data.get("models", [])]
        return cls(
            models=models,
            sensitivity_analysis=data.get("sensitivity_analysis"),
            robustness_metrics=data.get("robustness_metrics")
        )


def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of uncorrected p-values.

    Returns:
        List of corrected p-values (capped at 1.0).
    """
    n = len(p_values)
    if n == 0:
        return []

    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected


def main() -> None:
    """
    Main entry point for the results module (for testing).
    """
    # Example usage
    model = StatisticalModel(
        subfield="CA3",
        formula="vol ~ ACE + age",
        beta_ace=-0.05,
        ci_95_low=-0.10,
        ci_95_high=0.00,
        p_value=0.04,
        log_likelihood=-100.5,
        aic=205.0,
        bic=210.0,
        n_obs=500
    )

    p_vals = [0.04, 0.01, 0.05]
    corrected = apply_bonferroni_correction(p_vals)

    print(f"Original p-values: {p_vals}")
    print(f"Corrected p-values: {corrected}")


if __name__ == "__main__":
    main()
