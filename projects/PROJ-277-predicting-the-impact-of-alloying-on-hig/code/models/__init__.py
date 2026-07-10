"""
Machine learning models and training logic.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class AlloySample:
    """
    Represents a single alloy sample with its composition and properties.
    
    Attributes:
        elemental_composition: Dictionary mapping element symbols to weight percentages.
        thermodynamic_descriptors: Dictionary of calculated thermodynamic features 
            (e.g., oxide formation enthalpies, periodic table features).
        microstructural_features: Optional dictionary of microstructural data 
            (e.g., grain size, precipitate fraction).
        observed_weight_gain: The experimentally observed weight gain (mg/cm^2) 
            at high temperature.
    """
    elemental_composition: Dict[str, float]
    thermodynamic_descriptors: Dict[str, float]
    microstructural_features: Optional[Dict[str, float]] = None
    observed_weight_gain: float = 0.0
    
    def __post_init__(self) -> None:
        if self.observed_weight_gain < 0:
            raise ValueError("Observed weight gain cannot be negative.")


@dataclass
class PredictionResult:
    """
    Represents the output of a model prediction for an alloy sample.
    
    Attributes:
        predicted_weight_gain: The model's predicted weight gain (mg/cm^2).
        confidence_interval: A tuple (lower, upper) representing the confidence 
            interval for the prediction.
        model_type: String identifier of the model used (e.g., "RandomForest", 
            "GaussianProcess").
        feature_contributions: Dictionary mapping feature names to their 
            contribution values (e.g., SHAP values) for this prediction.
    """
    predicted_weight_gain: float
    confidence_interval: Tuple[float, float]
    model_type: str
    feature_contributions: Dict[str, float]
    
    def __post_init__(self) -> None:
        if self.confidence_interval[0] > self.confidence_interval[1]:
            raise ValueError("Confidence interval lower bound cannot be greater than upper bound.")


@dataclass
class GapAnalysisReport:
    """
    Represents the results of comparing composition-only models against 
    microstructure-augmented models.
    
    Attributes:
        composition_only_rmse: Root Mean Squared Error of the composition-only model.
        augmented_rmse: Root Mean Squared Error of the model augmented with 
            microstructural features.
        error_reduction_pct: Percentage reduction in RMSE achieved by adding 
            microstructural features.
        sensitive_samples: List of sample IDs that show high sensitivity to 
            microstructural features (e.g., error > 2x median).
    """
    composition_only_rmse: float
    augmented_rmse: float
    error_reduction_pct: float
    sensitive_samples: List[str]
    
    def __post_init__(self) -> None:
        if self.composition_only_rmse < 0 or self.augmented_rmse < 0:
            raise ValueError("RMSE values cannot be negative.")