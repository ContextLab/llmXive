"""
Data models for the llmXive JoyAI-VL-Interaction pipeline.

This module defines the core data structures used for:
1. SyntheticVideoFrame: Representing individual video frames with visual metadata.
2. InternalStateVector: Representing hidden states from the JoyAI-VL model.
3. SchedulerDecision: Representing the final intervention decision.

These models are aligned with the project plan and support streaming/batching
operations as required by the 6GB RAM constraint.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json


@dataclass
class SyntheticVideoFrame:
    """
    Represents a single frame in a synthetic video stream.

    Attributes:
        frame_id (str): Unique identifier for the frame.
        timestamp (float): Timestamp in seconds relative to video start.
        visual_features (Dict[str, Any]): Dictionary of visual features extracted
            from the frame (e.g., bounding boxes, object classes, depth maps).
        ground_truth_label (str): The ground-truth label derived strictly from
            visual content (e.g., 'fall', 'sitting', 'walking').
        is_critical (bool): Boolean flag indicating if the frame contains a
            critical event requiring intervention.
        raw_image_path (Optional[str]): Path to the raw image file on disk.
        metadata (Dict[str, Any]): Additional metadata (e.g., camera angle, lighting).
    """
    frame_id: str
    timestamp: float
    visual_features: Dict[str, Any] = field(default_factory=dict)
    ground_truth_label: str = "unknown"
    is_critical: bool = False
    raw_image_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the frame to a dictionary for JSON serialization."""
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "visual_features": self.visual_features,
            "ground_truth_label": self.ground_truth_label,
            "is_critical": self.is_critical,
            "raw_image_path": self.raw_image_path,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticVideoFrame':
        """Create a SyntheticVideoFrame instance from a dictionary."""
        return cls(
            frame_id=data["frame_id"],
            timestamp=data["timestamp"],
            visual_features=data.get("visual_features", {}),
            ground_truth_label=data.get("ground_truth_label", "unknown"),
            is_critical=data.get("is_critical", False),
            raw_image_path=data.get("raw_image_path"),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the frame to a JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class InternalStateVector:
    """
    Represents the internal state vector extracted from the JoyAI-VL model.

    This data structure captures hidden states and attention maps at a specific
    time step, excluding final token logits as per the project specification.

    Attributes:
        frame_id (str): Reference to the corresponding video frame ID.
        timestamp (float): Timestamp matching the frame.
        hidden_states (List[List[float]]): List of hidden state vectors from
            transformer layers. Shape: [num_layers, hidden_dim].
        attention_maps (List[List[float]]): List of attention weight matrices.
            Shape: [num_heads, seq_len, seq_len].
        layer_indices (List[int]): Indices of the layers from which states were
            extracted.
        attention_indices (List[int]): Indices of the attention heads used.
        extraction_time (datetime): Timestamp when the extraction was performed.
    """
    frame_id: str
    timestamp: float
    hidden_states: List[List[float]] = field(default_factory=list)
    attention_maps: List[List[float]] = field(default_factory=list)
    layer_indices: List[int] = field(default_factory=list)
    attention_indices: List[int] = field(default_factory=list)
    extraction_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state vector to a dictionary for JSON serialization."""
        # Convert datetime to ISO format string for JSON compatibility
        data = {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "hidden_states": self.hidden_states,
            "attention_maps": self.attention_maps,
            "layer_indices": self.layer_indices,
            "attention_indices": self.attention_indices,
            "extraction_time": self.extraction_time.isoformat()
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InternalStateVector':
        """Create an InternalStateVector instance from a dictionary."""
        return cls(
            frame_id=data["frame_id"],
            timestamp=data["timestamp"],
            hidden_states=data.get("hidden_states", []),
            attention_maps=data.get("attention_maps", []),
            layer_indices=data.get("layer_indices", []),
            attention_indices=data.get("attention_indices", []),
            extraction_time=datetime.fromisoformat(data.get("extraction_time", datetime.now().isoformat()))
        )

    def to_json(self) -> str:
        """Serialize the state vector to a JSON string."""
        return json.dumps(self.to_dict())

    def validate_dimensions(self, expected_layers: int, expected_heads: int) -> None:
        """
        Validate that the internal state dimensions match expectations.

        Args:
            expected_layers: Expected number of transformer layers.
            expected_heads: Expected number of attention heads.

        Raises:
            ValueError: If dimensions do not match.
        """
        if len(self.hidden_states) != expected_layers:
            raise ValueError(
                f"Dimension mismatch: Expected {expected_layers} layers, "
                f"Actual {len(self.hidden_states)} layers in hidden_states."
            )
        if len(self.attention_maps) != expected_heads:
            raise ValueError(
                f"Dimension mismatch: Expected {expected_heads} heads, "
                f"Actual {len(self.attention_maps)} heads in attention_maps."
            )


@dataclass
class SchedulerDecision:
    """
    Represents a decision made by the scheduler to intervene or not.

    Attributes:
        decision_id (str): Unique identifier for the decision.
        frame_id (str): Reference to the frame being evaluated.
        timestamp (float): Timestamp of the decision.
        predicted_label (str): The label predicted by the scheduler model.
        confidence_score (float): Confidence score of the prediction (0.0 to 1.0).
        intervention_required (bool): Final boolean decision on whether to intervene.
        reason (Optional[str]): Explanation for the decision (e.g., high confidence,
            rule-based override).
        model_version (str): Version of the scheduler model used.
        latency_ms (float): Inference latency in milliseconds.
    """
    decision_id: str
    frame_id: str
    timestamp: float
    predicted_label: str
    confidence_score: float
    intervention_required: bool
    reason: Optional[str] = None
    model_version: str = "unknown"
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the decision to a dictionary for JSON serialization."""
        return {
            "decision_id": self.decision_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "predicted_label": self.predicted_label,
            "confidence_score": self.confidence_score,
            "intervention_required": self.intervention_required,
            "reason": self.reason,
            "model_version": self.model_version,
            "latency_ms": self.latency_ms
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchedulerDecision':
        """Create a SchedulerDecision instance from a dictionary."""
        return cls(
            decision_id=data["decision_id"],
            frame_id=data["frame_id"],
            timestamp=data["timestamp"],
            predicted_label=data["predicted_label"],
            confidence_score=data["confidence_score"],
            intervention_required=data["intervention_required"],
            reason=data.get("reason"),
            model_version=data.get("model_version", "unknown"),
            latency_ms=data.get("latency_ms", 0.0)
        )

    def to_json(self) -> str:
        """Serialize the decision to a JSON string."""
        return json.dumps(self.to_dict())


# Type aliases for convenience in other modules
FrameList = List[SyntheticVideoFrame]
StateVectorList = List[InternalStateVector]
DecisionList = List[SchedulerDecision]