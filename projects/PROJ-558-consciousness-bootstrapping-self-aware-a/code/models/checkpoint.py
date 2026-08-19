"""
ModelCheckpoint entity for serializing model states and metadata.

This module defines the `ModelCheckpoint` dataclass, which serves as the
primary container for saving and loading model weights, optimizer states,
and associated training metadata. It is designed for strict serialization
compatibility (JSON for metadata, binary for tensors) and adheres to the
project's data hygiene principles.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path
import os
import torch
import hashlib

@dataclass
class ModelCheckpoint:
    """
    Represents a saved state of a model during or after training.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint (e.g., UUID or hash).
        model_name: Name of the model architecture (e.g., 'recursive_llama', 'baseline_llama').
        step: The training step number at which this checkpoint was saved.
        epoch: The epoch number at which this checkpoint was saved.
        timestamp: ISO 8601 formatted string of when the checkpoint was saved.
        config_snapshot: A dictionary of the hyperparameters and config used at this step.
        metrics_snapshot: A dictionary of training metrics at this step (loss, accuracy, etc.).
        state_dict_path: Relative path to the file containing the torch state_dict.
        optimizer_state_path: Relative path to the file containing the optimizer state.
        tags: Optional list of tags for categorization (e.g., 'best_val', 'final').
        checksum: SHA-256 checksum of the state_dict file for integrity verification.
    """
    checkpoint_id: str
    model_name: str
    step: int
    epoch: int
    timestamp: str
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    state_dict_path: Optional[str] = None
    optimizer_state_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the checkpoint metadata to a dictionary suitable for JSON serialization.
        Note: Binary tensors are excluded; only paths and metadata are included.
        """
        return {
            "checkpoint_id": self.checkpoint_id,
            "model_name": self.model_name,
            "step": self.step,
            "epoch": self.epoch,
            "timestamp": self.timestamp,
            "config_snapshot": self.config_snapshot,
            "metrics_snapshot": self.metrics_snapshot,
            "state_dict_path": self.state_dict_path,
            "optimizer_state_path": self.optimizer_state_path,
            "tags": self.tags,
            "checksum": self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCheckpoint':
        """
        Reconstructs a ModelCheckpoint from a dictionary.
        """
        return cls(
            checkpoint_id=data["checkpoint_id"],
            model_name=data["model_name"],
            step=data["step"],
            epoch=data["epoch"],
            timestamp=data["timestamp"],
            config_snapshot=data.get("config_snapshot", {}),
            metrics_snapshot=data.get("metrics_snapshot", {}),
            state_dict_path=data.get("state_dict_path"),
            optimizer_state_path=data.get("optimizer_state_path"),
            tags=data.get("tags", []),
            checksum=data.get("checksum")
        )

    def save_metadata(self, output_path: Path) -> None:
        """
        Saves the checkpoint metadata to a JSON file.

        Args:
            output_path: The file path where the metadata JSON will be written.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load_metadata(cls, input_path: Path) -> 'ModelCheckpoint':
        """
        Loads checkpoint metadata from a JSON file.

        Args:
            input_path: The file path to read the metadata from.

        Returns:
            A ModelCheckpoint instance populated with the file data.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Checkpoint metadata not found at {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

    def compute_checksum(self, state_dict_path: Path) -> str:
        """
        Computes the SHA-256 checksum of the state_dict file.

        Args:
            state_dict_path: Path to the binary state_dict file.

        Returns:
            Hexadecimal string of the SHA-256 hash.
        """
        sha256_hash = hashlib.sha256()
        with open(state_dict_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        self.checksum = sha256_hash.hexdigest()
        return self.checksum
