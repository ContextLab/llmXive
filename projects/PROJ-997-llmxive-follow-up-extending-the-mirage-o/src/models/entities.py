from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json

@dataclass
class TrainingSample:
    """
    Represents a single data point in the hardware-validated gap dataset.
    Contains features extracted from full-precision training and ground-truth
    measurements from quantized inference.
    """
    input_id: str
    gradient_norms: float
    local_curvature: float
    quantized_logits: List[float]
    calculated_kl_divergence: float
    quantization_level: str  # e.g., "INT4", "INT8", "FP8"
    input_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary for serialization."""
        return {
            "input_id": self.input_id,
            "gradient_norms": self.gradient_norms,
            "local_curvature": self.local_curvature,
            "quantized_logits": self.quantized_logits,
            "calculated_kl_divergence": self.calculated_kl_divergence,
            "quantization_level": self.quantization_level,
            "input_text": self.input_text,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the sample to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingSample":
        """Create a TrainingSample instance from a dictionary."""
        return cls(
            input_id=data["input_id"],
            gradient_norms=data["gradient_norms"],
            local_curvature=data["local_curvature"],
            quantized_logits=data["quantized_logits"],
            calculated_kl_divergence=data["calculated_kl_divergence"],
            quantization_level=data["quantization_level"],
            input_text=data.get("input_text"),
            metadata=data.get("metadata", {})
        )


@dataclass
class GapPredictionResult:
    """
    Represents the output of the training-signal predictor model.
    Contains the predicted gap and associated confidence metrics.
    """
    input_id: str
    predicted_gap: float
    actual_gap: Optional[float] = None
    features_used: Dict[str, float] = field(default_factory=dict)
    model_version: Optional[str] = None
    inference_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "input_id": self.input_id,
            "predicted_gap": self.predicted_gap,
            "actual_gap": self.actual_gap,
            "features_used": self.features_used,
            "model_version": self.model_version,
            "inference_time_ms": self.inference_time_ms
        }

    def to_json(self) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GapPredictionResult":
        """Create a GapPredictionResult instance from a dictionary."""
        return cls(
            input_id=data["input_id"],
            predicted_gap=data["predicted_gap"],
            actual_gap=data.get("actual_gap"),
            features_used=data.get("features_used", {}),
            model_version=data.get("model_version"),
            inference_time_ms=data.get("inference_time_ms")
        )

    def error(self) -> Optional[float]:
        """Calculate the absolute error if actual gap is available."""
        if self.actual_gap is not None:
            return abs(self.predicted_gap - self.actual_gap)
        return None