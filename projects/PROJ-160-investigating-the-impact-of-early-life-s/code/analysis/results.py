"""
Results module for statistical analysis outputs.

Defines base entity definitions for analysis results and statistical models
used in the early life stress impact study.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import numpy as np


class ModelType(Enum):
    """Enumeration of supported statistical model types."""
    LINEAR_MIXED_EFFECTS = "LMM"
    LINEAR_REGRESSION = "LM"
    PERMUTATION_TEST = "Permutation"


@dataclass
class StatisticalModel:
    """
    Data class representing a fitted statistical model and its core metrics.

    Attributes:
        model_type: Type of statistical model used (e.g., LMM).
        formula: The model formula string (e.g., 'y ~ x + z').
        dependent_variable: Name of the dependent variable.
        independent_variables: List of independent variable names.
        beta_coefficients: Dictionary mapping variable names to beta coefficients.
        standard_errors: Dictionary mapping variable names to standard errors.
        confidence_intervals: Dictionary mapping variable names to (lower, upper) CI tuples.
        p_values: Dictionary mapping variable names to uncorrected p-values.
        corrected_p_values: Dictionary mapping variable names to Bonferroni-corrected p-values.
        model_fit_stats: Dictionary of additional fit statistics (AIC, BIC, R-squared, etc.).
        sample_size: Number of observations used in the model.
        degrees_of_freedom: Degrees of freedom for the model.
    """
    model_type: ModelType
    formula: str
    dependent_variable: str
    independent_variables: List[str]
    beta_coefficients: Dict[str, float] = field(default_factory=dict)
    standard_errors: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, tuple] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    corrected_p_values: Dict[str, float] = field(default_factory=dict)
    model_fit_stats: Dict[str, float] = field(default_factory=dict)
    sample_size: Optional[int] = None
    degrees_of_freedom: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model object to a dictionary for serialization."""
        return {
            "model_type": self.model_type.value,
            "formula": self.formula,
            "dependent_variable": self.dependent_variable,
            "independent_variables": self.independent_variables,
            "beta_coefficients": self.beta_coefficients,
            "standard_errors": self.standard_errors,
            "confidence_intervals": {
                k: list(v) if isinstance(v, tuple) else v
                for k, v in self.confidence_intervals.items()
            },
            "p_values": self.p_values,
            "corrected_p_values": self.corrected_p_values,
            "model_fit_stats": self.model_fit_stats,
            "sample_size": self.sample_size,
            "degrees_of_freedom": self.degrees_of_freedom
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the model to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatisticalModel":
        """Create a StatisticalModel instance from a dictionary."""
        # Convert string model type back to Enum
        if isinstance(data.get("model_type"), str):
            data["model_type"] = ModelType(data["model_type"])
        
        # Reconstruct confidence intervals from lists back to tuples if needed
        if "confidence_intervals" in data:
            data["confidence_intervals"] = {
                k: tuple(v) if isinstance(v, list) else v
                for k, v in data["confidence_intervals"].items()
            }
        
        return cls(**data)


@dataclass
class AnalysisResult:
    """
    Data class representing the complete result of a specific analysis.

    This entity encapsulates the model, the data context, and the interpretation
    flags required for the study.

    Attributes:
        analysis_id: Unique identifier for this analysis run.
        subfield: The hippocampal subfield analyzed (e.g., 'CA3', 'DG', 'Subiculum').
        model: The StatisticalModel object containing the fit results.
        covariates_used: List of covariates included in the model.
        normalization_method: Method used for volume normalization (e.g., 'ICV').
        transformation_applied: Description of any data transformation (e.g., 'log').
        interpretation: Textual interpretation of the findings (associational only).
        is_significant_after_correction: Boolean indicating if any result survived correction.
        metadata: Additional metadata about the analysis run.
    """
    analysis_id: str
    subfield: str
    model: StatisticalModel
    covariates_used: List[str]
    normalization_method: str
    transformation_applied: Optional[str] = None
    interpretation: str = ""
    is_significant_after_correction: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and set derived fields after initialization."""
        if not self.interpretation:
            self._generate_default_interpretation()
        
        self._check_significance()

    def _generate_default_interpretation(self):
        """Generate a default interpretation string based on the model results."""
        significant_vars = [
            var for var, p in self.model.corrected_p_values.items()
            if p < 0.05
        ]
        
        if significant_vars:
            vars_str = ", ".join(significant_vars)
            self.interpretation = (
                f"Associational analysis indicates a significant relationship between "
                f"{vars_str} and {self.subfield} volume (p < 0.05, Bonferroni corrected). "
                f"Note: This is an associational finding, not causal."
            )
        else:
            self.interpretation = (
                f"No statistically significant associations were found between the "
                f"independent variables and {self.subfield} volume after Bonferroni correction "
                f"(p >= 0.05). Note: This is an associational analysis."
            )

    def _check_significance(self):
        """Update the is_significant_after_correction flag based on model results."""
        self.is_significant_after_correction = any(
            p < 0.05 for p in self.model.corrected_p_values.values()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis result to a dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "subfield": self.subfield,
            "model": self.model.to_dict(),
            "covariates_used": self.covariates_used,
            "normalization_method": self.normalization_method,
            "transformation_applied": self.transformation_applied,
            "interpretation": self.interpretation,
            "is_significant_after_correction": self.is_significant_after_correction,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the analysis result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create an AnalysisResult instance from a dictionary."""
        model_data = data.get("model", {})
        model = StatisticalModel.from_dict(model_data)
        
        return cls(
            analysis_id=data.get("analysis_id"),
            subfield=data.get("subfield"),
            model=model,
            covariates_used=data.get("covariates_used", []),
            normalization_method=data.get("normalization_method"),
            transformation_applied=data.get("transformation_applied"),
            interpretation=data.get("interpretation", ""),
            is_significant_after_correction=data.get("is_significant_after_correction", False),
            metadata=data.get("metadata", {})
        )

    def summary_report(self) -> str:
        """Generate a human-readable summary report of the analysis."""
        lines = [
            f"Analysis Result: {self.analysis_id}",
            f"Subfield: {self.subfield}",
            f"Model Type: {self.model.model_type.value}",
            f"Formula: {self.model.formula}",
            f"Sample Size: {self.model.sample_size}",
            "",
            "Coefficients:",
        ]
        
        for var, beta in self.model.beta_coefficients.items():
            se = self.model.standard_errors.get(var, 0.0)
            p_uncorr = self.model.p_values.get(var, 1.0)
            p_corr = self.model.corrected_p_values.get(var, 1.0)
            
            ci = self.model.confidence_intervals.get(var, (0.0, 0.0))
            ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]"
            
            lines.append(
                f"  {var}: β={beta:.4f} (SE={se:.4f}), 95% CI={ci_str}, "
                f"p={p_uncorr:.4f}, p_corr={p_corr:.4f}"
            )
        
        lines.append("")
        lines.append(f"Interpretation: {self.interpretation}")
        
        return "\n".join(lines)
