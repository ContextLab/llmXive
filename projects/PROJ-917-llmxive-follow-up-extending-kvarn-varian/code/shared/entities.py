"""
Shared entity definitions for the llmXive KVarN follow-up project.

This module defines the core data structures used across data generation,
model training, and simulation modules to ensure type consistency and
data integrity.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class AttentionTrajectory:
    """
    Represents a single attention trajectory over time steps.
    
    Attributes:
        trajectory_id: Unique identifier for this trajectory.
        steps: Number of time steps in the trajectory.
        moments: Dictionary containing statistical moments for each step.
            Keys: 'mean', 'var', 'skew', 'kurt'
            Values: List of floats, one per step.
        scaling_factor: Ground-truth scaling factor computed for this trajectory.
        drift_model: Name of the drift model applied (e.g., 'linear', 'exponential').
        drift_params: Dictionary of parameters used for the drift model.
        created_at: Timestamp of trajectory creation.
        checksum: SHA-256 checksum of the trajectory data for integrity verification.
    """
    trajectory_id: str
    steps: int
    moments: Dict[str, List[float]]
    scaling_factor: float
    drift_model: str = "linear"
    drift_params: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None

    def __post_init__(self):
        """Validate moments structure and compute checksum if not provided."""
        required_keys = ['mean', 'var', 'skew', 'kurt']
        for key in required_keys:
            if key not in self.moments:
                raise ValueError(f"Missing required moment: {key}")
            if len(self.moments[key]) != self.steps:
                raise ValueError(f"Moment '{key}' length {len(self.moments[key])} != steps {self.steps}")
        
        if self.checksum is None:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Compute SHA-256 checksum of trajectory data."""
        data_dict = {
            'trajectory_id': self.trajectory_id,
            'steps': self.steps,
            'moments': self.moments,
            'scaling_factor': self.scaling_factor,
            'drift_model': self.drift_model,
            'drift_params': self.drift_params
        }
        # Sort keys for deterministic serialization
        json_str = json.dumps(data_dict, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'trajectory_id': self.trajectory_id,
            'steps': self.steps,
            'moments': self.moments,
            'scaling_factor': self.scaling_factor,
            'drift_model': self.drift_model,
            'drift_params': self.drift_params,
            'created_at': self.created_at.isoformat(),
            'checksum': self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttentionTrajectory':
        """Load from dictionary."""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)

    def save(self, path: Union[str, Path]) -> None:
        """Save trajectory to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved trajectory {self.trajectory_id} to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'AttentionTrajectory':
        """Load trajectory from JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Trajectory file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        trajectory = cls.from_dict(data)
        
        # Verify checksum
        if trajectory.checksum != trajectory._compute_checksum():
            logger.warning(f"Checksum mismatch for trajectory {trajectory.trajectory_id}")
        
        return trajectory

@dataclass
class ScalingFactor:
    """
    Represents a scaling factor prediction or ground truth value.
    
    Attributes:
        factor_id: Unique identifier for this scaling factor record.
        trajectory_id: Reference to the parent trajectory.
        step_index: The time step index this factor applies to.
        value: The scaling factor value.
        method: Method used to compute this factor (e.g., 'sinkhorn', 'static_prior', 'closed_form').
        input_moments: Dictionary of moments used to compute this factor.
        computed_at: Timestamp of computation.
    """
    factor_id: str
    trajectory_id: str
    step_index: int
    value: float
    method: str
    input_moments: Dict[str, float] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'factor_id': self.factor_id,
            'trajectory_id': self.trajectory_id,
            'step_index': self.step_index,
            'value': self.value,
            'method': self.method,
            'input_moments': self.input_moments,
            'computed_at': self.computed_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScalingFactor':
        """Load from dictionary."""
        if 'computed_at' in data and isinstance(data['computed_at'], str):
            data['computed_at'] = datetime.fromisoformat(data['computed_at'])
        
        return cls(**data)

    def save(self, path: Union[str, Path]) -> None:
        """Save scaling factor to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'ScalingFactor':
        """Load scaling factor from JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Scaling factor file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

@dataclass
class SimulationRun:
    """
    Represents a complete simulation run with accumulated metrics.
    
    Attributes:
        run_id: Unique identifier for this simulation run.
        config: Dictionary of simulation configuration parameters.
        steps: Total number of steps executed.
        accumulated_kl_divergence: Total KL-divergence accumulated over the run.
        average_kl_per_step: Average KL-divergence per step.
        accumulated_error: Total error accumulated over the run.
        average_error_per_step: Average error per step.
        timing_metrics: Dictionary of timing information (total time, per-step time).
        method: The optimization method used (e.g., 'kvarn', 'static_prior').
        seed: Random seed used for reproducibility.
        start_time: When the run started.
        end_time: When the run completed.
        status: Run status ('completed', 'failed', 'interrupted').
        error_message: Error message if the run failed.
    """
    run_id: str
    config: Dict[str, Any]
    steps: int
    accumulated_kl_divergence: float
    average_kl_per_step: float
    accumulated_error: float
    average_error_per_step: float
    timing_metrics: Dict[str, float] = field(default_factory=dict)
    method: str = "kvarn"
    seed: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "completed"
    error_message: Optional[str] = None

    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.end_time is None and self.status == "completed":
            self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'run_id': self.run_id,
            'config': self.config,
            'steps': self.steps,
            'accumulated_kl_divergence': self.accumulated_kl_divergence,
            'average_kl_per_step': self.average_kl_per_step,
            'accumulated_error': self.accumulated_error,
            'average_error_per_step': self.average_error_per_step,
            'timing_metrics': self.timing_metrics,
            'method': self.method,
            'seed': self.seed,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'error_message': self.error_message
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRun':
        """Load from dictionary."""
        # Handle datetime conversion
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        
        return cls(**data)

    def save(self, path: Union[str, Path]) -> None:
        """Save simulation run results to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved simulation run {self.run_id} to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'SimulationRun':
        """Load simulation run results from JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Simulation run file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

    def update_metrics(self, 
                     kl_divergence: float, 
                     error: float, 
                     step_time: float) -> None:
        """
        Update accumulated metrics with new step data.
        
        Args:
            kl_divergence: KL-divergence for the current step.
            error: Error for the current step.
            step_time: Time taken for the current step.
        """
        self.accumulated_kl_divergence += kl_divergence
        self.accumulated_error += error
        self.steps += 1
        self.average_kl_per_step = self.accumulated_kl_divergence / self.steps
        self.average_error_per_step = self.accumulated_error / self.steps
        
        if 'step_times' not in self.timing_metrics:
            self.timing_metrics['step_times'] = []
        self.timing_metrics['step_times'].append(step_time)
        
        self.timing_metrics['total_time'] = sum(self.timing_metrics['step_times'])
        self.timing_metrics['avg_step_time'] = (
            self.timing_metrics['total_time'] / self.steps
        )

    def mark_failed(self, error_message: str) -> None:
        """Mark the simulation run as failed."""
        self.status = "failed"
        self.error_message = error_message
        self.end_time = datetime.now()
        logger.error(f"Simulation run {self.run_id} failed: {error_message}")