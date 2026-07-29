"""
Model checkpoint definitions for the Consciousness Bootstrapping project.
Provides the ModelCheckpoint dataclass to serialize training state and metadata.
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
    Dataclass representing a saved model checkpoint.
    
    Attributes:
        model_type: Type of model (e.g., 'recursive', 'baseline')
        recursion_depth: Depth of recursion used during training
        seed: Random seed used for reproducibility
        epoch: Epoch number when checkpoint was saved
        step: Global training step count
        loss: Final training loss value
        config: Dictionary of hyperparameters used
        state_dict_path: Path to the actual PyTorch state dict file
        created_at: Timestamp of checkpoint creation
        metadata: Additional arbitrary metadata
    """
    model_type: str
    recursion_depth: int
    seed: int
    epoch: int
    step: int
    loss: float
    config: Dict[str, Any]
    state_dict_path: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert checkpoint to JSON string."""
        data = {
            'model_type': self.model_type,
            'recursion_depth': self.recursion_depth,
            'seed': self.seed,
            'epoch': self.epoch,
            'step': self.step,
            'loss': self.loss,
            'config': self.config,
            'state_dict_path': self.state_dict_path,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
        return json.dumps(data, indent=2)
    
    def save_metadata(self, output_path: str) -> None:
        """Save checkpoint metadata to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_metadata(cls, input_path: str) -> 'ModelCheckpoint':
        """Load checkpoint metadata from a JSON file."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint metadata not found: {input_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate that required fields are present and state_dict exists."""
        if not self.model_type:
            return False
        if not self.state_dict_path or not Path(self.state_dict_path).exists():
            return False
        if self.recursion_depth < 0:
            return False
        return True
