"""
Base data model classes for the llmXive Moebius pipeline.

Defines core data structures for masked regions, inference results,
and gating states used throughout the system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class MaskedRegion:
    """
    Represents a masked region within an image.

    Attributes:
        image_id: Unique identifier for the source image.
        mask: Binary mask (H, W) where 1 indicates the masked region.
        gradient_variance: Variance of gradients in the masked region.
        texture_entropy: Entropy measure of texture complexity in the masked region.
        coordinates: Bounding box coordinates (y_min, x_min, y_max, x_max).
        complexity_score: Pre-computed complexity score (1-5) if available.
    """
    image_id: str
    mask: np.ndarray
    gradient_variance: float
    texture_entropy: float
    coordinates: Tuple[int, int, int, int]
    complexity_score: Optional[float] = None

    def __post_init__(self):
        if self.mask.ndim != 2:
            raise ValueError(f"Mask must be 2D, got {self.mask.ndim}D")
        if self.gradient_variance < 0:
            raise ValueError("gradient_variance cannot be negative")
        if self.texture_entropy < 0:
            raise ValueError("texture_entropy cannot be negative")


@dataclass
class InferenceResult:
    """
    Stores the output of a single inference pass.

    Attributes:
        image_id: ID of the processed image.
        reconstructed_image: The inpainted image array (H, W, C).
        latency_ms: Wall-clock time taken for inference in milliseconds.
        rank_used: The rank value used by the gating mechanism.
        fidelity_metrics: Dictionary of quality metrics (e.g., FID, LPIPS).
        gating_state: The gating state associated with this result.
    """
    image_id: str
    reconstructed_image: np.ndarray
    latency_ms: float
    rank_used: int
    fidelity_metrics: Dict[str, float] = field(default_factory=dict)
    gating_state: Optional['GatingState'] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary for JSON serialization."""
        return {
            "image_id": self.image_id,
            "latency_ms": self.latency_ms,
            "rank_used": self.rank_used,
            "fidelity_metrics": self.fidelity_metrics,
            "gating_state": self.gating_state.to_dict() if self.gating_state else None
        }


@dataclass
class GatingState:
    """
    Represents the internal state of the gating mechanism.

    Attributes:
        input_complexity: The raw complexity score derived from mask metrics.
        predicted_rank: The rank selected by the gating head.
        confidence: Confidence score of the rank prediction (0.0-1.0).
        parameters: Dictionary of internal parameters used for this decision.
    """
    input_complexity: float
    predicted_rank: int
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not (1 <= self.predicted_rank <= 5):
            raise ValueError(f"predicted_rank must be between 1 and 5, got {self.predicted_rank}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dictionary for JSON serialization."""
        return {
            "input_complexity": self.input_complexity,
            "predicted_rank": self.predicted_rank,
            "confidence": self.confidence,
            "parameters": self.parameters
        }