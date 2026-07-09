from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class ModelCheckpoint:
    """
    Dataclass representing a saved model state and metadata.
    Used to track training progress, model configurations, and evaluation metrics at specific steps.
    """
    checkpoint_id: str
    model_name: str
    step: int
    epoch: int
    timestamp: datetime
    config: dict
    metrics: dict = field(default_factory=dict)
    loss: Optional[float] = None
    validation_loss: Optional[float] = None
    model_path: Optional[str] = None
    optimizer_state_path: Optional[str] = None
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "model_name": self.model_name,
            "step": self.step,
            "epoch": self.epoch,
            "timestamp": self.timestamp.isoformat(),
            "config": self.config,
            "metrics": self.metrics,
            "loss": self.loss,
            "validation_loss": self.validation_loss,
            "model_path": self.model_path,
            "optimizer_state_path": self.optimizer_state_path,
            "tags": self.tags,
            "metadata": self.metadata
        }

    def save_to_json(self, path: str) -> None:
        """Save checkpoint metadata to a JSON file."""
        data = self.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, path: str) -> 'ModelCheckpoint':
        """Load checkpoint metadata from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert timestamp string back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
