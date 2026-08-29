from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path
import os

@dataclass
class ModelCheckpoint:
    """
    Represents a saved model state during or after training.
    Suitable for serialization to JSON (metadata) and binary (weights).
    """
    checkpoint_id: str
    model_type: str  # e.g., 'recursive_llama', 'baseline_llama'
    timestamp: datetime = field(default_factory=datetime.now)
    epoch: int = 0
    step: int = 0
    loss: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    artifact_path: Optional[str] = None  # Path to the .bin or .pt file
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            'checkpoint_id': self.checkpoint_id,
            'model_type': self.model_type,
            'timestamp': self.timestamp.isoformat(),
            'epoch': self.epoch,
            'step': self.step,
            'loss': self.loss,
            'metrics': self.metrics,
            'config_snapshot': self.config_snapshot,
            'artifact_path': self.artifact_path,
            'metadata': self.metadata
        }

    def save_metadata(self, output_dir: Path) -> None:
        """Save the metadata portion of the checkpoint to a JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / f"{self.checkpoint_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCheckpoint':
        """Reconstruct from a dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            checkpoint_id=data['checkpoint_id'],
            model_type=data['model_type'],
            timestamp=timestamp,
            epoch=data.get('epoch', 0),
            step=data.get('step', 0),
            loss=data.get('loss'),
            metrics=data.get('metrics', {}),
            config_snapshot=data.get('config_snapshot', {}),
            artifact_path=data.get('artifact_path'),
            metadata=data.get('metadata', {})
        )
