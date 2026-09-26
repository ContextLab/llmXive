from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

@dataclass
class ExtractionDataset:
    """Schema for extracted (UI_state, Corrective_Hint, Action) triples."""
    triples: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def save(self, path: Path) -> None:
        """Save dataset to JSON/Parquet."""
        data = {
            "triples": self.triples,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'ExtractionDataset':
        """Load dataset from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        instance = cls()
        instance.triples = data.get("triples", [])
        instance.metadata = data.get("metadata", {})
        instance.created_at = data.get("created_at", "")
        return instance

@dataclass
class DistilledModel:
    """Schema for distilled model artifacts."""
    model_id: str
    config: Dict[str, Any]
    weights_path: Path
    training_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def save_metadata(self, path: Path) -> None:
        """Save model metadata."""
        data = {
            "model_id": self.model_id,
            "config": self.config,
            "weights_path": str(self.weights_path),
            "training_metrics": self.training_metrics,
            "created_at": self.created_at
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

@dataclass
class EvaluationResult:
    """Schema for evaluation results."""
    task_id: str
    model_id: str
    success: bool
    steps: int
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "model_id": self.model_id,
            "success": self.success,
            "steps": self.steps,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }