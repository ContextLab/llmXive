"""
Base data structures for the analysis pipeline.

Defines core entities: SyntheticDataset, ImputationResult, and CausalEstimate.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd


@dataclass
class SyntheticDataset:
    """
    Represents a synthetic dataset generated for the study.
    
    Attributes:
        X: Feature matrix (numpy array or pandas DataFrame)
        T: Treatment assignment vector (numpy array or pandas Series)
        Y: Outcome vector (numpy array or pandas Series) - may contain NaNs if missingness injected
        ground_truth_ate: The true Average Treatment Effect used to generate the data
        seed: Random seed used for generation
        beta: The MNAR parameter used (if applicable)
        missing_mask: Optional boolean mask indicating missing values in Y
    """
    X: Any
    T: Any
    Y: Any
    ground_truth_ate: float
    seed: int
    beta: Optional[float] = None
    missing_mask: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset to a dictionary representation."""
        return {
            "X": self.X,
            "T": self.T,
            "Y": self.Y,
            "ground_truth_ate": self.ground_truth_ate,
            "seed": self.seed,
            "beta": self.beta,
        }


@dataclass
class CausalEstimate:
    """
    Represents a single causal effect estimate.
    
    Attributes:
        method: Name of the imputation method used (e.g., "mean", "knn", "mice")
        estimator: Name of the causal estimator used (e.g., "ipw", "psm")
        ate: Point estimate of the Average Treatment Effect
        se: Standard error of the estimate
        ci_lower: Lower bound of the confidence interval
        ci_upper: Upper bound of the confidence interval
        confidence_level: Confidence level used (e.g., 0.95)
        metadata: Additional metadata dictionary
    """
    method: str
    estimator: str
    ate: float
    se: float
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    metadata: Dict[str, Any] = field(default_factory=dict)

    def contains_truth(self, truth: float) -> bool:
        """Check if the confidence interval contains the ground truth."""
        return self.ci_lower <= truth <= self.ci_upper

    def absolute_bias(self, truth: float) -> float:
        """Calculate absolute bias relative to ground truth."""
        return abs(self.ate - truth)


@dataclass
class ImputationResult:
    """
    Represents the result of an imputation operation.
    
    Attributes:
        method: Name of the imputation method used
        original_data: The original incomplete dataset (SyntheticDataset)
        imputed_data: The completed dataset (SyntheticDataset with no NaNs)
        metadata: Additional metadata about the imputation process
    """
    method: str
    original_data: SyntheticDataset
    imputed_data: SyntheticDataset
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate that imputed data has no NaNs in Y
        if hasattr(self.imputed_data.Y, 'isna'):
            if self.imputed_data.Y.isna().any():
                raise ValueError("Imputed data Y contains NaNs.")
        elif hasattr(self.imputed_data.Y, 'mask'):
            # Check for np.nan
            if np.isnan(self.imputed_data.Y).any():
                raise ValueError("Imputed data Y contains NaNs.")