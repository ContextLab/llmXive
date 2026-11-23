from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class ModelType(Enum):
    LINEAR_ADDITIVE = "linear_additive"
    LINEAR_INTERACTION = "linear_interaction"
    POLYNOMIAL = "polynomial"

@dataclass
class RegressionModel:
    """
    Represents a statistical model for analyzing cooperative segregation effects.
    """
    model_type: ModelType
    features: List[str]
    coefficients: Dict[str, float]
    interaction_terms: List[str] = field(default_factory=list)
    r_squared: Optional[float] = None
    mse: Optional[float] = None
    p_values: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "features": self.features,
            "coefficients": self.coefficients,
            "interaction_terms": self.interaction_terms,
            "r_squared": self.r_squared,
            "mse": self.mse,
            "p_values": self.p_values,
            "metadata": self.metadata
        }
