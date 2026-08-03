from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class MaskedRegion:
    """
    Represents a masked region in an image.
    
    Attributes:
        image_id: Unique identifier for the source image.
        mask_path: File path to the binary mask (0=background, 1=hole).
        complexity_score: Float score (1-5) indicating visual complexity of the masked region.
        metrics: Dictionary storing computed features (e.g., gradient_variance, texture_entropy).
    """
    image_id: str
    mask_path: str
    complexity_score: float
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "image_id": self.image_id,
            "mask_path": self.mask_path,
            "complexity_score": self.complexity_score,
            "metrics": self.metrics
        }

@dataclass
class InferenceResult:
    """
    Result of an inference run for a specific masked region.
    
    Attributes:
        image_id: Unique identifier for the source image.
        latency_ms: Wall-clock time taken for inference in milliseconds.
        fidelity_score: Quality metric (e.g., LPIPS, FID component) comparing output to ground truth.
        rank_used: The integer rank selected by the gating mechanism for this region.
        metrics: Additional metrics (e.g., PSNR, SSIM).
    """
    image_id: str
    latency_ms: float
    fidelity_score: float
    rank_used: int
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "image_id": self.image_id,
            "latency_ms": self.latency_ms,
            "fidelity_score": self.fidelity_score,
            "rank_used": self.rank_used,
            "metrics": self.metrics
        }

@dataclass
class GatingState:
    """
    State of the gating mechanism for a specific inference step.
    
    Attributes:
        complexity_input: The input complexity score (1-5) used to drive the gate.
        predicted_rank: The integer rank (e.g., 1 to 5) predicted by the gating head.
        confidence: Confidence score (0.0-1.0) of the rank prediction.
        parameters: Dictionary of internal parameters used by the gating logic 
                    (e.g., interpolation weights, threshold values).
    """
    complexity_input: float
    predicted_rank: int
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "complexity_input": self.complexity_input,
            "predicted_rank": self.predicted_rank,
            "confidence": self.confidence,
            "parameters": self.parameters
        }