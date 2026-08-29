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
    
    Schema: 128x128 matrix (float32), mean (float32), variance (float32), 
    sparsity (float32 ratio of zero elements), outlier_magnitude (float32).
    """
    matrix: np.ndarray
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float

    def __post_init__(self):
        """Validate matrix dimensions and numerical properties."""
        # Ensure matrix is 128x128
        if self.matrix.shape != (128, 128):
            raise ValueError(f"AttentionMatrix must be 128x128, got {self.matrix.shape}")
        
        # Ensure dtype is float32
        if self.matrix.dtype != np.float32:
            self.matrix = self.matrix.astype(np.float32)
        
        # Validate scalar fields
        if not np.isfinite(self.mean):
            raise ValueError(f"Mean must be finite, got {self.mean}")
        if not np.isfinite(self.variance):
            raise ValueError(f"Variance must be finite, got {self.variance}")
        if not (0.0 <= self.sparsity <= 1.0):
            raise ValueError(f"Sparsity must be in [0, 1], got {self.sparsity}")
        if not np.isfinite(self.outlier_magnitude):
            raise ValueError(f"Outlier magnitude must be finite, got {self.outlier_magnitude}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'matrix': self.matrix.tolist(),
            'mean': float(self.mean),
            'variance': float(self.variance),
            'sparsity': float(self.sparsity),
            'outlier_magnitude': float(self.outlier_magnitude)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttentionMatrix':
        """Reconstruct from dictionary."""
        return cls(
            matrix=np.array(data['matrix'], dtype=np.float32),
            mean=float(data['mean']),
            variance=float(data['variance']),
            sparsity=float(data['sparsity']),
            outlier_magnitude=float(data['outlier_magnitude'])
        )

@dataclass
class ScalingFactor:
    """
    Represents a scaling factor derived for an attention matrix.
    
    Schema: Scalar value, derivation_method.
    """
    value: float
    derivation_method: str

    def __post_init__(self):
        """Validate the scaling factor properties."""
        if not np.isfinite(self.value):
            raise ValueError(f"Scaling factor value must be finite, got {self.value}")
        if not isinstance(self.derivation_method, str) or not self.derivation_method.strip():
            raise ValueError("derivation_method must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'value': float(self.value),
            'derivation_method': self.derivation_method
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScalingFactor':
        """Reconstruct from dictionary."""
        return cls(
            value=float(data['value']),
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
            # Recalculate to ensure consistency
            calculated_sum = sum(self.kl_divergence_sequence)
            # Allow small floating point tolerance
            if abs(self.accumulated_kl - calculated_sum) > 1e-9:
                self.accumulated_kl = calculated_sum

    def to_dict(self) -> Dict[str, Any]:
        return {
            'run_id': self.run_id,
            'seed': self.seed,
            'steps': self.steps,
            'kl_divergence_sequence': self.kl_divergence_sequence,
            'timing_metrics': self.timing_metrics,
            'accumulated_kl': float(self.accumulated_kl),
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