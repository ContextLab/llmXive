from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import numpy as np
import json

class NormalizationMethod(Enum):
    """Enumeration for data normalization strategies."""
    ARCHARD_K = "archard_k"
    RAW = "raw"
    NORMALIZED = "normalized"

@dataclass
class LSTRecord:
    """
    Data entity representing a single Laser Surface Texturing (LST) experimental record.
    Maps to the canonical columns defined in the project schema.
    """
    # Predictors (Features)
    pulse_duration: Optional[float] = None
    power: Optional[float] = None
    scanning_speed: Optional[float] = None
    pattern_geometry: Optional[str] = None
    
    # Material Properties
    hardness: Optional[float] = None
    elastic_modulus: Optional[float] = None
    
    # Test Conditions (Optional predictors, required for Archard normalization)
    contact_load: Optional[float] = None
    sliding_speed: Optional[float] = None
    
    # Target
    wear_rate: Optional[float] = None
    
    # Metadata & Flags
    source_id: Optional[str] = None
    normalization_method: NormalizationMethod = NormalizationMethod.RAW
    wear_coefficient: Optional[float] = None  # K calculated via Archard's Law
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary, handling Enum serialization."""
        d = self.__dict__.copy()
        d['normalization_method'] = self.normalization_method.value
        return d

@dataclass
class ModelPerformance:
    """
    Data entity storing the performance metrics of a trained regression model.
    """
    model_name: str
    r2_score: float
    mae: float
    rmse: float
    cv_scores: List[float] = field(default_factory=list)
    lomo_r2: Optional[float] = None
    transferability_ratio: Optional[float] = None
    is_best: bool = False
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

@dataclass
class FeatureImportance:
    """
    Data entity storing feature importance data derived from SHAP or permutation importance.
    """
    feature_name: str
    importance_score: float
    shap_mean_abs: Optional[float] = None
    shap_interaction_score: Optional[float] = None
    p_value: Optional[float] = None
    is_significant: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()