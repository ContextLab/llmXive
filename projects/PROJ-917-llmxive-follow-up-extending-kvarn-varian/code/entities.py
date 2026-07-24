from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
from pathlib import Path
import json
from datetime import datetime

@dataclass
class AttentionMatrix:
    """
    Represents a synthetic or real attention matrix with extracted statistical properties.
    
    Schema: 128x128 matrix, mean, variance, sparsity, outlier_magnitude.
    """
    matrix: np.ndarray
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'matrix': self.matrix.tolist(),
            'mean': self.mean,
            'variance': self.variance,
            'sparsity': self.sparsity,
            'outlier_magnitude': self.outlier_magnitude
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttentionMatrix':
        """Reconstruct from dictionary."""
        return cls(
            matrix=np.array(data['matrix']),
            mean=data['mean'],
            variance=data['variance'],
            sparsity=data['sparsity'],
            outlier_magnitude=data['outlier_magnitude']
        )

@dataclass
class ScalingFactor:
    """
    Represents a scaling factor derived for an attention matrix.
    
    Schema: Scalar value, derivation_method.
    """
    value: float
    derivation_method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'derivation_method': self.derivation_method
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScalingFactor':
        return cls(
            value=data['value'],
            derivation_method=data['derivation_method']
        )

@dataclass
class SimulationRun:
    """
    Represents the complete state and results of a single simulation run.
    
    Schema: Sequence of KL-divergence values, timing metrics.
    """
    run_id: str
    seed: int
    steps: int
    kl_divergence_sequence: List[float]
    timing_metrics: Dict[str, float]
    accumulated_kl: float
    start_time: str
    end_time: str
    method: str
    config_snapshot: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Ensure accumulated_kl is consistent with the sequence."""
        if not self.kl_divergence_sequence:
            self.accumulated_kl = 0.0
        else:
            # Recalculate to ensure consistency if not provided or mismatched
            self.accumulated_kl = sum(self.kl_divergence_sequence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'run_id': self.run_id,
            'seed': self.seed,
            'steps': self.steps,
            'kl_divergence_sequence': self.kl_divergence_sequence,
            'timing_metrics': self.timing_metrics,
            'accumulated_kl': self.accumulated_kl,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'method': self.method,
            'config_snapshot': self.config_snapshot
        }

    def to_json(self, path: Union[str, Path]) -> None:
        """Serialize the run to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'SimulationRun':
        """Load a run from a JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            run_id=data['run_id'],
            seed=data['seed'],
            steps=data['steps'],
            kl_divergence_sequence=data['kl_divergence_sequence'],
            timing_metrics=data['timing_metrics'],
            accumulated_kl=data['accumulated_kl'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            method=data['method'],
            config_snapshot=data.get('config_snapshot')
        )
    def __post_init__(self):
        """Ensure accumulated_kl is consistent with the sequence."""
        if not self.kl_divergence_sequence:
            self.accumulated_kl = 0.0
        else:
            # Recalculate to ensure consistency if not provided or mismatched
            self.accumulated_kl = sum(self.kl_divergence_sequence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'run_id': self.run_id,
            'seed': self.seed,
            'steps': self.steps,
            'kl_divergence_sequence': self.kl_divergence_sequence,
            'timing_metrics': self.timing_metrics,
            'accumulated_kl': self.accumulated_kl,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'method': self.method,
            'config_snapshot': self.config_snapshot
        }

    def to_json(self, path: Union[str, Path]) -> None:
        """Serialize the run to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'SimulationRun':
        """Load a run from a JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            run_id=data['run_id'],
            seed=data['seed'],
            steps=data['steps'],
            kl_divergence_sequence=data['kl_divergence_sequence'],
            timing_metrics=data['timing_metrics'],
            accumulated_kl=data['accumulated_kl'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            method=data['method'],
            config_snapshot=data.get('config_snapshot')
        )