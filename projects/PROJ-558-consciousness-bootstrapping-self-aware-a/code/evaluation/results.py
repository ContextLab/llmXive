"""
Evaluation result definitions for the Consciousness Bootstrapping project.
Provides the EvaluationResult dataclass to store benchmark outputs and metrics.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class EvaluationResult:
    """
    Dataclass representing the results of a model evaluation run.
    
    Attributes:
        model_path: Path to the evaluated model checkpoint
        model_type: Type of model ('recursive' or 'baseline')
        dataset: Name of the dataset evaluated (e.g., 'gsm8k', 'mmlu')
        seed: Random seed used for evaluation
        timestamp: When the evaluation was run
        metrics: Dictionary of computed metrics (self-consistency, brier, etc.)
        predictions: List of prediction records (question, answer, confidence, correct)
        calibration_data: Calibration curve data (bins, counts, accuracies)
        error_detection: Error detection calibration results
        raw_outputs: Raw model outputs for debugging
        metadata: Additional evaluation metadata
    """
    model_path: str
    model_type: str
    dataset: str
    seed: int
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    calibration_data: Optional[Dict[str, List[float]]] = None
    error_detection: Optional[Dict[str, Any]] = None
    raw_outputs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to a dictionary for JSON serialization."""
        data = {
            'model_path': self.model_path,
            'model_type': self.model_type,
            'dataset': self.dataset,
            'seed': self.seed,
            'timestamp': self.timestamp.isoformat(),
            'metrics': self.metrics,
            'predictions': self.predictions,
            'calibration_data': self.calibration_data,
            'error_detection': self.error_detection,
            'raw_outputs': self.raw_outputs,
            'metadata': self.metadata
        }
        return data
    
    def to_json(self) -> str:
        """Convert evaluation result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, output_path: str) -> None:
        """Save evaluation result to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, input_path: str) -> 'EvaluationResult':
        """Load evaluation result from a JSON file."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation result not found: {input_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate that required fields are present."""
        if not self.model_path:
            return False
        if not self.model_type:
            return False
        if not self.dataset:
            return False
        if self.seed is None:
            return False
        return True