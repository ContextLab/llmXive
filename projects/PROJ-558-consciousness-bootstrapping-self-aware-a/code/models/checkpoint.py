"""
ModelCheckpoint entity for serialization.

This module defines the data structure used to save and load model checkpoints
during the training and evaluation process. It adheres to the project's
serialization requirements and Constitution Principle III (Data Hygiene).
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
    Represents a snapshot of a model's state at a specific point in training.

    Attributes:
        id: Unique identifier for this checkpoint.
        model_type: The type of model (e.g., 'recursive_llama', 'baseline_llama').
        model_name: The name of the pre-trained model used (e.g., 'TinyLlama-1.1B').
        checkpoint_path: Absolute path to the saved model weights file.
        epoch: The training epoch number when this checkpoint was saved.
        global_step: The total number of optimization steps performed.
        loss: The loss value at this checkpoint.
        metrics: A dictionary of additional metrics recorded at this checkpoint.
        config_snapshot: A dictionary snapshot of the configuration used during training.
        created_at: Timestamp of when the checkpoint was created.
        metadata: Additional arbitrary metadata.
    """
    id: str
    model_type: str
    model_name: str
    checkpoint_path: str
    epoch: int
    global_step: int
    loss: float
    metrics: Dict[str, float] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the checkpoint to a dictionary for JSON serialization.

        Returns:
            A dictionary representation of the checkpoint.
        """
        return {
            'id': self.id,
            'model_type': self.model_type,
            'model_name': self.model_name,
            'checkpoint_path': self.checkpoint_path,
            'epoch': self.epoch,
            'global_step': self.global_step,
            'loss': self.loss,
            'metrics': self.metrics,
            'config_snapshot': self.config_snapshot,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Converts the checkpoint to a JSON string.

        Args:
            indent: Indentation level for pretty printing.

        Returns:
            A JSON string representation of the checkpoint.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCheckpoint':
        """
        Creates a ModelCheckpoint instance from a dictionary.

        Args:
            data: A dictionary containing checkpoint data.

        Returns:
            A ModelCheckpoint instance.
        """
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data['id'],
            model_type=data['model_type'],
            model_name=data['model_name'],
            checkpoint_path=data['checkpoint_path'],
            epoch=data['epoch'],
            global_step=data['global_step'],
            loss=data['loss'],
            metrics=data.get('metrics', {}),
            config_snapshot=data.get('config_snapshot', {}),
            created_at=created_at,
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelCheckpoint':
        """
        Creates a ModelCheckpoint instance from a JSON string.

        Args:
            json_str: A JSON string containing checkpoint data.

        Returns:
            A ModelCheckpoint instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_metadata(self, output_dir: str) -> str:
        """
        Saves the checkpoint metadata to a JSON file.

        Args:
            output_dir: The directory where the metadata file will be saved.

        Returns:
            The path to the saved metadata file.
        """
        output_path = Path(output_dir) / f"{self.id}_metadata.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return str(output_path)

    @classmethod
    def load_metadata(cls, file_path: str) -> 'ModelCheckpoint':
        """
        Loads a checkpoint metadata from a JSON file.

        Args:
            file_path: The path to the metadata file.

        Returns:
            A ModelCheckpoint instance.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
