"""
Data model for trained machine learning models and their metadata.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


@dataclass
class Model:
    """
    Represents a trained machine learning model and its evaluation metrics.

    Attributes:
        model_id: Unique identifier for the model instance.
        model_type: Type of model (e.g., 'RandomForest', 'SVM').
        hyperparameters: Dictionary of hyperparameters used for training.
        training_date: Timestamp of when the model was trained.
        metrics: Dictionary of performance metrics (AUC, accuracy, etc.).
        feature_importance: List of (feature_name, importance_score) tuples.
        artifact_path: Path to the saved model file (e.g., pickle/Joblib).
        metadata: Additional context (e.g., training set size, version).
    """
    model_id: str
    model_type: str
    hyperparameters: Dict[str, Any]
    training_date: str
    metrics: Dict[str, float]
    feature_importance: List[Dict[str, Any]] = field(default_factory=list)
    artifact_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.model_id:
            raise ValueError("model_id cannot be empty")
        if not self.model_type:
            raise ValueError("model_type cannot be empty")
        if not self.training_date:
            self.training_date = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "hyperparameters": self.hyperparameters,
            "training_date": self.training_date,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "artifact_path": self.artifact_path,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the model to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def add_metric(self, name: str, value: float) -> None:
        """Add or update a performance metric."""
        self.metrics[name] = value

    def add_feature_importance(self, feature_name: str, score: float) -> None:
        """Add a feature importance entry."""
        self.feature_importance.append({
            "feature_name": feature_name,
            "score": score
        })