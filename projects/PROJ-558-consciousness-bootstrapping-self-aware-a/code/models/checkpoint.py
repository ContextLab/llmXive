"""
ModelCheckpoint entity for serialization.

Defines the structure for saving and loading model training states,
including metadata, metrics, and configuration snapshots.
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
    Represents a saved state of a model during or after training.
    
    Attributes:
        checkpoint_id: Unique identifier for this checkpoint.
        model_name: Name of the model architecture (e.g., 'recursive_llama').
        epoch: The training epoch number when this checkpoint was saved.
        step: The global training step number.
        loss: The final loss value at this checkpoint.
        metrics: Dictionary of additional metrics (accuracy, self_consistency, etc.).
        config_snapshot: Snapshot of the configuration used during training.
        path: Filesystem path where the checkpoint weights are stored.
        created_at: Timestamp of creation.
        metadata: Additional arbitrary metadata.
    """
    checkpoint_id: str
    model_name: str
    epoch: int
    step: int
    loss: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the checkpoint to a dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "model_name": self.model_name,
            "epoch": self.epoch,
            "step": self.step,
            "loss": self.loss,
            "metrics": self.metrics,
            "config_snapshot": self.config_snapshot,
            "path": self.path,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the checkpoint to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelCheckpoint":
        """Load a checkpoint from a dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            model_name=data["model_name"],
            epoch=data["epoch"],
            step=data["step"],
            loss=data["loss"],
            metrics=data.get("metrics", {}),
            config_snapshot=data.get("config_snapshot", {}),
            path=data.get("path"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ModelCheckpoint":
        """Load a checkpoint from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_metadata(self, output_dir: str) -> str:
        """
        Save the checkpoint metadata to a JSON file in the specified directory.
        
        Args:
            output_dir: Directory path to save the metadata file.
            
        Returns:
            The full path to the saved metadata file.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"checkpoint_{self.checkpoint_id}_metadata.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        
        return filepath
