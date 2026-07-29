"""
ModelCheckpoint entity for serialization of training artifacts.

This module defines the `ModelCheckpoint` dataclass, which encapsulates
the metadata and state required to serialize and restore model training progress.
It is designed to satisfy Constitution Principle III (Data Hygiene) by including
checksums and timestamps.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ModelCheckpoint:
    """
    Represents a saved model checkpoint.

    Attributes:
        model_type: The type of model (e.g., 'recursive_llama', 'baseline_llama').
        checkpoint_id: Unique identifier for this checkpoint.
        epoch: The epoch number at which this checkpoint was saved.
        step: The global step number.
        loss: The loss value at this checkpoint.
        config: Snapshot of the configuration used for training.
        state_dict_path: Path to the actual model weights file (serialized separately).
        metadata: Additional metadata (e.g., recursion depth, seed).
        timestamp: ISO format timestamp of when the checkpoint was created.
        checksum: SHA-256 checksum of the weights file (for integrity verification).
    """
    model_type: str
    checkpoint_id: str
    epoch: int
    step: int
    loss: float
    config: Dict[str, Any]
    state_dict_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the checkpoint to a dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "checkpoint_id": self.checkpoint_id,
            "epoch": self.epoch,
            "step": self.step,
            "loss": self.loss,
            "config": self.config,
            "state_dict_path": self.state_dict_path,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "checksum": self.checksum
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the checkpoint to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelCheckpoint":
        """Deserialize a checkpoint from a dictionary."""
        return cls(
            model_type=data["model_type"],
            checkpoint_id=data["checkpoint_id"],
            epoch=data["epoch"],
            step=data["step"],
            loss=data["loss"],
            config=data["config"],
            state_dict_path=data["state_dict_path"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            checksum=data.get("checksum")
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ModelCheckpoint":
        """Deserialize a checkpoint from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save_metadata(self, output_dir: Path) -> Path:
        """
        Save the checkpoint metadata to a JSON file in the specified directory.
        Returns the path to the saved metadata file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{self.checkpoint_id}_metadata.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return file_path
