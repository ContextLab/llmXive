from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path
import os

@dataclass
class ModelCheckpoint:
    """
    Represents a saved model state with metadata for reproducibility and tracking.
    Used to serialize training states, model weights, and configuration snapshots.
    """
    checkpoint_id: str
    model_type: str  # e.g., 'recursive', 'baseline'
    architecture: str  # e.g., 'TinyLlama-1.1B'
    recursion_depth: int
    epoch: int
    step: int
    loss: float
    metrics: Dict[str, float] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for JSON serialization."""
        return {
            'checkpoint_id': self.checkpoint_id,
            'model_type': self.model_type,
            'architecture': self.architecture,
            'recursion_depth': self.recursion_depth,
            'epoch': self.epoch,
            'step': self.step,
            'loss': self.loss,
            'metrics': self.metrics,
            'config_snapshot': self.config_snapshot,
            'created_at': self.created_at.isoformat(),
            'file_path': self.file_path,
            'checksum': self.checksum,
            'tags': self.tags
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize checkpoint to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_metadata(self, output_dir: str) -> Path:
        """
        Save checkpoint metadata to a JSON file in the specified directory.
        Returns the path to the saved file.
        """
        output_path = Path(output_dir) / f"{self.checkpoint_id}_metadata.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return output_path

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelCheckpoint':
        """Create a ModelCheckpoint instance from a dictionary."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    @classmethod
    def load_metadata(cls, file_path: str) -> 'ModelCheckpoint':
        """Load checkpoint metadata from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint metadata file not found: {file_path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
