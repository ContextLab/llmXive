from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class ModelCheckpoint:
    """
    Dataclass to represent a model checkpoint.
    
    Attributes:
        path: Path to the saved checkpoint file.
        epoch: The epoch number when the checkpoint was saved.
        step: The global training step number.
        loss: The training loss at this checkpoint.
        metrics: Dictionary of additional metrics at this checkpoint.
        timestamp: ISO format timestamp of when the checkpoint was created.
        model_config: Configuration dictionary used to create the model.
        metadata: Arbitrary metadata dictionary.
    """
    path: str
    epoch: int
    step: int
    loss: float
    metrics: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model_config: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert the checkpoint to a dictionary for serialization."""
        return {
            "path": self.path,
            "epoch": self.epoch,
            "step": self.step,
            "loss": self.loss,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "model_config": self.model_config,
            "metadata": self.metadata
        }

    def save_metadata(self, output_dir: str) -> Path:
        """
        Save the checkpoint metadata to a JSON file.
        
        Args:
            output_dir: Directory to save the metadata file.
            
        Returns:
            Path to the saved metadata file.
        """
        output_path = Path(output_dir) / f"checkpoint_{self.epoch}_{self.step}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return output_path

    @classmethod
    def load_metadata(cls, path: str) -> "ModelCheckpoint":
        """
        Load a checkpoint metadata from a JSON file.
        
        Args:
            path: Path to the checkpoint metadata JSON file.
            
        Returns:
            ModelCheckpoint instance.
        """
        with open(path, "r") as f:
            data = json.load(f)
        
        return cls(
            path=data["path"],
            epoch=data["epoch"],
            step=data["step"],
            loss=data["loss"],
            metrics=data.get("metrics", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            model_config=data.get("model_config", {}),
            metadata=data.get("metadata", {})
        )
