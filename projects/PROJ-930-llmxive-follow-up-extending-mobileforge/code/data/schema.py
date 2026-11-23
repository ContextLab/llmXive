from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

@dataclass
class ExtractionDataset:
    """Represents the extracted dataset of (UI_state, Hint, Action) triples."""
    path: Path
    count: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "count": self.count,
            "created_at": self.created_at.isoformat()
        }
    
    def save_metadata(self) -> None:
        """Saves the dataset metadata to a JSON file alongside the dataset."""
        metadata_path = self.path.with_suffix(self.path.suffix + '.meta.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_metadata(cls, metadata_path: Path) -> 'ExtractionDataset':
        """Loads dataset metadata from a JSON file."""
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        return cls(
            path=Path(data['path']),
            count=data['count'],
            created_at=datetime.fromisoformat(data['created_at'])
        )

@dataclass
class DistilledModel:
    """Represents the trained distilled model."""
    path: Path
    config: Dict[str, Any]
    weights_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "config": self.config,
            "weights_hash": self.weights_hash,
            "created_at": self.created_at.isoformat()
        }
    
    def save_metadata(self) -> None:
        """Saves the model metadata to a JSON file alongside the model weights."""
        metadata_path = self.path.with_suffix('.meta.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_metadata(cls, metadata_path: Path) -> 'DistilledModel':
        """Loads model metadata from a JSON file."""
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        return cls(
            path=Path(data['path']),
            config=data['config'],
            weights_hash=data.get('weights_hash'),
            created_at=datetime.fromisoformat(data['created_at'])
        )

@dataclass
class EvaluationResult:
    """Represents the result of an evaluation run."""
    model_path: Path
    dataset_path: Path
    metrics: Dict[str, float]
    p_value: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_path": str(self.model_path),
            "dataset_path": str(self.dataset_path),
            "metrics": self.metrics,
            "p_value": self.p_value,
            "created_at": self.created_at.isoformat()
        }
    
    def save_report(self, output_path: Path) -> None:
        """Saves the evaluation result as a JSON report."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_report(cls, report_path: Path) -> 'EvaluationResult':
        """Loads an evaluation result from a JSON report file."""
        with open(report_path, 'r') as f:
            data = json.load(f)
        return cls(
            model_path=Path(data['model_path']),
            dataset_path=Path(data['dataset_path']),
            metrics=data['metrics'],
            p_value=data.get('p_value'),
            created_at=datetime.fromisoformat(data['created_at'])
        )