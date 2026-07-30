"""
ModelCheckpoint entity for serialization of training state.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path
import os


@dataclass
class ModelCheckpoint:
    """
    Represents a saved model checkpoint with metadata for reproducibility.
    """
    checkpoint_id: str
    model_type: str  # e.g., 'recursive', 'baseline'
    epoch: int
    step: int
    loss: float
    metrics: Dict[str, float]
    config_snapshot: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    path: Optional[str] = None  # Relative path to the .pt or .safetensors file
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "model_type": self.model_type,
            "epoch": self.epoch,
            "step": self.step,
            "loss": self.loss,
            "metrics": self.metrics,
            "config_snapshot": self.config_snapshot,
            "created_at": self.created_at,
            "path": self.path
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCheckpoint':
        """Deserialize from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            model_type=data["model_type"],
            epoch=data["epoch"],
            step=data["step"],
            loss=data["loss"],
            metrics=data["metrics"],
            config_snapshot=data["config_snapshot"],
            created_at=data.get("created_at", datetime.now().isoformat()),
            path=data.get("path")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelCheckpoint':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_metadata(self, output_dir: str) -> str:
        """
        Save the checkpoint metadata to a JSON file in the specified directory.
        Returns the path to the saved file.
        """
        path = Path(output_dir) / f"{self.checkpoint_id}_metadata.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return str(path)
