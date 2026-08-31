"""Schema for ModelArtifact contract."""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ModelArtifact:
    """Contract for trained model artifacts."""
    model_name: str
    model_type: str
    metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    config: Optional[Dict[str, Any]] = None
    path: Optional[str] = None