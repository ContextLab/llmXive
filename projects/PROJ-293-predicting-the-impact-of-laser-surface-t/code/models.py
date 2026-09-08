"""
Data models and entities for the LST Wear Resistance prediction pipeline.

This module defines the core data structures for:
- LSTRecord: Represents a single experimental observation of laser surface texturing.
- ModelPerformance: Stores metrics and configuration for a trained regression model.
- FeatureImportance: Stores the importance scores and statistical significance of features.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class NormalizationMethod(Enum):
    """Enum for normalization methods applied to wear data."""
    ARCHARD = "archard"
    RAW = "raw"


@dataclass
class LSTRecord:
    """
    Represents a single experimental record from LST wear studies.

    Attributes:
        pulse_duration (float): Laser pulse duration (ns).
        power (float): Laser power (W).
        scanning_speed (float): Scanning speed (mm/s).
        pattern_geometry (str): Geometry of the texturing pattern (e.g., 'dimples', 'grooves').
        hardness (float): Material hardness (HV).
        elastic_modulus (float): Elastic modulus (GPa).
        wear_rate (float): Measured wear rate (mm^3/Nm).
        contact_load (Optional[float]): Contact load (N), may be missing for raw records.
        sliding_speed (Optional[float]): Sliding speed (m/s), may be missing for raw records.
        normalization_method (NormalizationMethod): Method used to normalize wear data.
        material_class (str): Class of the material (e.g., 'steel', 'ceramic') for LOMO validation.
        source_id (str): Unique identifier for the source study or dataset row.
    """
    pulse_duration: float
    power: float
    scanning_speed: float
    pattern_geometry: str
    hardness: float
    elastic_modulus: float
    wear_rate: float
    contact_load: Optional[float] = None
    sliding_speed: Optional[float] = None
    normalization_method: NormalizationMethod = NormalizationMethod.RAW
    material_class: str = "unknown"
    source_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a dictionary for serialization."""
        return {
            "pulse_duration": self.pulse_duration,
            "power": self.power,
            "scanning_speed": self.scanning_speed,
            "pattern_geometry": self.pattern_geometry,
            "hardness": self.hardness,
            "elastic_modulus": self.elastic_modulus,
            "wear_rate": self.wear_rate,
            "contact_load": self.contact_load,
            "sliding_speed": self.sliding_speed,
            "normalization_method": self.normalization_method.value,
            "material_class": self.material_class,
            "source_id": self.source_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LSTRecord":
        """Create a record from a dictionary."""
        norm_method = data.get("normalization_method", "raw")
        if isinstance(norm_method, str):
            norm_method = NormalizationMethod(norm_method)
        elif not isinstance(norm_method, NormalizationMethod):
            raise ValueError(f"Invalid normalization_method: {norm_method}")

        return cls(
            pulse_duration=data["pulse_duration"],
            power=data["power"],
            scanning_speed=data["scanning_speed"],
            pattern_geometry=data["pattern_geometry"],
            hardness=data["hardness"],
            elastic_modulus=data["elastic_modulus"],
            wear_rate=data["wear_rate"],
            contact_load=data.get("contact_load"),
            sliding_speed=data.get("sliding_speed"),
            normalization_method=norm_method,
            material_class=data.get("material_class", "unknown"),
            source_id=data.get("source_id", "")
        )


@dataclass
class ModelPerformance:
    """
    Stores performance metrics and configuration for a trained model.

    Attributes:
        model_name (str): Name of the algorithm (e.g., 'RandomForest').
        r2_score (float): Coefficient of determination (R²).
        mae (float): Mean Absolute Error.
        rmse (float): Root Mean Square Error.
        hyperparameters (Dict[str, Any]): Final hyperparameters used.
        training_time (float): Time taken to train in seconds.
        is_best (bool): Whether this model was selected as the best performer.
        lomo_r2 (Optional[float]): R² score from Leave-One-Material-Class-Out validation.
        transferability_failure (bool): True if LOMO performance dropped significantly.
    """
    model_name: str
    r2_score: float
    mae: float
    rmse: float
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_time: float = 0.0
    is_best: bool = False
    lomo_r2: Optional[float] = None
    transferability_failure: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert performance metrics to a dictionary."""
        return {
            "model_name": self.model_name,
            "r2_score": self.r2_score,
            "mae": self.mae,
            "rmse": self.rmse,
            "hyperparameters": self.hyperparameters,
            "training_time": self.training_time,
            "is_best": self.is_best,
            "lomo_r2": self.lomo_r2,
            "transferability_failure": self.transferability_failure
        }


@dataclass
class FeatureImportance:
    """
    Stores feature importance data derived from SHAP or permutation testing.

    Attributes:
        feature_name (str): Name of the feature.
        importance_score (float): Mean absolute SHAP value or permutation importance.
        rank (int): Rank of the feature (1 is most important).
        p_value (Optional[float]): P-value from conditional permutation testing.
        is_significant (bool): True if p_value < 0.05 (if p_value is available).
        interaction_magnitude (Optional[float]): Magnitude of non-linear interaction (SHAP interaction).
    """
    feature_name: str
    importance_score: float
    rank: int
    p_value: Optional[float] = None
    is_significant: bool = False
    interaction_magnitude: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert feature importance to a dictionary."""
        return {
            "feature_name": self.feature_name,
            "importance_score": self.importance_score,
            "rank": self.rank,
            "p_value": self.p_value,
            "is_significant": self.is_significant,
            "interaction_magnitude": self.interaction_magnitude
        }