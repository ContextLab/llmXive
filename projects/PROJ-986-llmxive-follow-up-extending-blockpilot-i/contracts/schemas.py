from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class FeatureVector:
    sample_id: str
    prompt_length: float
    mean_attention_entropy: float
    hidden_state_norm: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GroundTruth:
    sample_id: str
    optimal_block_size: int
    latencies: Dict[int, float]
    winner: int

@dataclass
class Prediction:
    sample_id: str
    predicted_block_size: int
    confidence: float
    features: FeatureVector

@dataclass
class ModelArtifact:
    model_type: str
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    trained_at: str
    feature_importance: Optional[Dict[str, float]] = None
