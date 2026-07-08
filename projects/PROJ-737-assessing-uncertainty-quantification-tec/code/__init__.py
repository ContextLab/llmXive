# llmXive Materials UQ Pipeline
__version__ = "0.1.0"

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class MaterialsDataset:
    """
    Container for a processed materials dataset.
    
    Attributes:
        name: Unique identifier for the dataset (e.g., 'oqmd_band_gap')
        X: Feature matrix (numpy array)
        y: Target values (numpy array)
        sample_ids: List of unique identifiers for each sample
        metadata: Dictionary containing dataset provenance and stats
    """
    name: str
    X: np.ndarray
    y: np.ndarray
    sample_ids: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        # Basic validation
        if self.X.shape[0] != len(self.y):
            raise ValueError(f"X ({self.X.shape[0]}) and y ({len(self.y)}) shape mismatch")
        if len(self.sample_ids) != self.X.shape[0]:
            raise ValueError(f"X ({self.X.shape[0]}) and sample_ids ({len(self.sample_ids)}) length mismatch")

    def __len__(self):
        return len(self.y)

@dataclass
class UQMethod:
    """
    Container for a configured Uncertainty Quantification method.
    
    Attributes:
        name: Unique identifier for the method (e.g., 'gpr_rbf', 'mc_dropout')
        model: The underlying scikit-learn or torch model instance
        config: Dictionary of hyperparameters used
        predictions: Array of point predictions (filled after inference)
        uncertainties: Array of uncertainty estimates (filled after inference)
        intervals: Array of prediction intervals [lower, upper] (filled after inference)
    """
    name: str
    model: Any
    config: Dict[str, Any]
    predictions: Optional[np.ndarray] = None
    uncertainties: Optional[np.ndarray] = None
    intervals: Optional[np.ndarray] = None

    def set_predictions(self, preds: np.ndarray, uncertainties: np.ndarray, intervals: np.ndarray):
        """Helper to populate inference results."""
        self.predictions = preds
        self.uncertainties = uncertainties
        self.intervals = intervals

@dataclass
class EvaluationMetric:
    """
    Container for a calculated evaluation metric.
    
    Attributes:
        name: Name of the metric (e.g., 'calibration_error', 'sharpness')
        dataset_name: Name of the dataset this metric was calculated on
        method_name: Name of the UQ method this metric belongs to
        value: The calculated numerical value
        nominal_level: The target confidence level if applicable (e.g., 0.95)
    """
    name: str
    dataset_name: str
    method_name: str
    value: float
    nominal_level: Optional[float] = None