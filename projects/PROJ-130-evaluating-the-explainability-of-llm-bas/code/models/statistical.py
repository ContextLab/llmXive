"""
Statistical result entities for the llmXive bug fix explainability pipeline.

This module defines the data structures used to store the results of
statistical analyses (correlations, AUC-ROC, p-values) performed on
the explainability scores and correctness labels.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StatisticalResult:
    """
    Represents the outcome of a statistical test comparing explainability
    metrics against bug fix correctness.

    Attributes:
        correlation_coeff (Optional[float]): The correlation coefficient
            (e.g., point-biserial) between an explainability score and
            the binary correctness label.
        auc_roc (Optional[float]): The Area Under the Receiver Operating
            Characteristic curve when using the explainability score to
            predict correctness.
        p_value (Optional[float]): The p-value resulting from the statistical
            test (e.g., t-test or significance test for correlation).
        test_type (str): A string identifier for the specific test performed
            (e.g., 'point_biserial', 'auc_roc', 'paired_ttest').
        method_name (str): The name of the explainability method associated
            with this result (e.g., 'attention', 'saliency', 'coherence').
    """
    correlation_coeff: Optional[float] = None
    auc_roc: Optional[float] = None
    p_value: Optional[float] = None
    test_type: str = "general"
    method_name: str = "unknown"

    def to_dict(self) -> dict:
        """Converts the dataclass instance to a dictionary for serialization."""
        return {
            "correlation_coeff": self.correlation_coeff,
            "auc_roc": self.auc_roc,
            "p_value": self.p_value,
            "test_type": self.test_type,
            "method_name": self.method_name
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StatisticalResult":
        """Creates a StatisticalResult instance from a dictionary."""
        return cls(
            correlation_coeff=data.get("correlation_coeff"),
            auc_roc=data.get("auc_roc"),
            p_value=data.get("p_value"),
            test_type=data.get("test_type", "general"),
            method_name=data.get("method_name", "unknown")
        )