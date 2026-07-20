from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
from pathlib import Path
import json
from datetime import datetime

@dataclass
class ScalingFactor:
    """
    Represents a single optimal scaling factor for a specific attention step.
    
    Attributes:
        step_index (int): The temporal index of the step in the trajectory.
        value (float): The computed scaling factor value.
        method (str): The method used to compute the factor (e.g., 'sinkhorn', 'static_prior').
        timestamp (float): Unix timestamp when this factor was computed.
    """
    step_index: int
    value: float
    method: str = "sinkhorn"
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "value": self.value,
            "method": self.method,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScalingFactor":
        return cls(
            step_index=data["step_index"],
            value=data["value"],
            method=data.get("method", "sinkhorn"),
            timestamp=data.get("timestamp", datetime.now().timestamp())
        )


@dataclass
class AttentionTrajectory:
    """
    Represents a sequence of attention steps (a trajectory) with their moments.
    
    This class stores a list of 128x128 matrices (as flattened arrays or references)
    and their temporal moments (mean, variance) per step. It also tracks the 
    computed scaling factors for each step.
    
    Attributes:
        trajectory_id (str): Unique identifier for this trajectory.
        steps (int): Total number of steps in the trajectory.
        matrix_size (int): Dimension of the square attention matrices (default 128).
        moments (List[Dict[str, float]]): List of moment dictionaries per step.
            Each dict contains: {"mean": float, "var": float}
        matrices (List[np.ndarray]): List of attention matrices (128x128).
            Stored as numpy arrays. If memory is constrained, these might be
            loaded on demand or stored as file paths, but for this entity,
            we assume they are held in memory or represented by their raw data.
        scaling_factors (List[ScalingFactor]): List of scaling factors computed
            for each step in the trajectory.
        drift_params (Optional[Dict[str, Any]]): Parameters used to generate
            the temporal drift for this trajectory (e.g., {'type': 'linear', 'slope': 0.1}).
        created_at (datetime): Timestamp of creation.
    """
    trajectory_id: str
    steps: int
    matrix_size: int = 128
    moments: List[Dict[str, float]] = field(default_factory=list)
    matrices: List[np.ndarray] = field(default_factory=list)
    scaling_factors: List[ScalingFactor] = field(default_factory=list)
    drift_params: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Ensure matrices and moments are consistent with step count if initialized
        # This is a safety check; actual population happens via add_step
        if len(self.matrices) != self.steps and self.steps > 0:
            # In a real implementation, we might resize or warn, but for now
            # we assume the caller manages the lists correctly or uses add_step.
            pass

    def add_step(
        self, 
        matrix: np.ndarray, 
        mean: float, 
        var: float, 
        scaling_factor: Optional[ScalingFactor] = None
    ) -> None:
        """
        Adds a new step to the trajectory.
        
        Args:
            matrix (np.ndarray): The 128x128 attention matrix.
            mean (float): Mean of the matrix elements.
            var (float): Variance of the matrix elements.
            scaling_factor (ScalingFactor, optional): Pre-computed scaling factor.
        """
        if matrix.shape != (self.matrix_size, self.matrix_size):
            raise ValueError(
                f"Matrix shape {matrix.shape} does not match expected {self.matrix_size}x{self.matrix_size}"
            )
        
        self.matrices.append(matrix)
        self.moments.append({"mean": mean, "var": var})
        
        if scaling_factor is None:
            # If no factor provided, create a placeholder or compute later
            # For now, we just track the step index.
            sf = ScalingFactor(
                step_index=len(self.scaling_factors),
                value=np.nan, # Placeholder
                method="pending"
            )
            self.scaling_factors.append(sf)
        else:
            # Ensure the step_index matches the current length
            scaling_factor.step_index = len(self.scaling_factors)
            self.scaling_factors.append(scaling_factor)

    def get_moments_for_step(self, step_idx: int) -> Dict[str, float]:
        """Retrieves mean and variance for a specific step."""
        if 0 <= step_idx < len(self.moments):
            return self.moments[step_idx]
        raise IndexError(f"Step index {step_idx} out of range for trajectory with {len(self.moments)} steps")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the trajectory to a dictionary.
        Note: Large matrices are not fully serialized in JSON for efficiency.
        Instead, we store the shape and a checksum or path if persisted.
        For this entity, we return metadata and moments.
        """
        return {
            "trajectory_id": self.trajectory_id,
            "steps": self.steps,
            "matrix_size": self.matrix_size,
            "moments": self.moments,
            "scaling_factors": [sf.to_dict() for sf in self.scaling_factors],
            "drift_params": self.drift_params,
            "created_at": self.created_at.isoformat(),
            # Matrices are omitted from dict representation to avoid huge JSON blobs.
            # They should be stored in binary formats (npz, parquet) separately.
            "has_matrices": len(self.matrices) > 0,
            "matrix_shape": list(self.matrices[0].shape) if self.matrices else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttentionTrajectory":
        """
        Deserializes a trajectory from a dictionary.
        Note: Matrices cannot be reconstructed from this dict alone.
        """
        return cls(
            trajectory_id=data["trajectory_id"],
            steps=data["steps"],
            matrix_size=data.get("matrix_size", 128),
            moments=data.get("moments", []),
            matrices=[], # Must be loaded separately
            scaling_factors=[
                ScalingFactor.from_dict(sf) for sf in data.get("scaling_factors", [])
            ],
            drift_params=data.get("drift_params"),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class SimulationRun:
    """
    Represents a single execution of the autoregressive simulation loop.
    
    Attributes:
        run_id (str): Unique identifier for the run.
        seed (int): Random seed used for this run.
        total_steps (int): Number of steps simulated.
        method (str): Method used for scaling factor prediction (e.g., 'sinkhorn', 'static_prior').
        accumulated_kl_divergence (float): Total KL divergence accumulated over the run.
        per_step_kl (List[float]): KL divergence at each step.
        per_step_latency (List[float]): Wall-clock time per step in seconds.
        avg_latency (float): Average latency per step.
        config_snapshot (Dict[str, Any]): Snapshot of the configuration used.
        completed_at (datetime): Timestamp of completion.
        status (str): 'completed', 'failed', 'interrupted'.
        error_message (Optional[str]): Error details if status is 'failed'.
    """
    run_id: str
    seed: int
    total_steps: int
    method: str
    accumulated_kl_divergence: float = 0.0
    per_step_kl: List[float] = field(default_factory=list)
    per_step_latency: List[float] = field(default_factory=list)
    avg_latency: float = 0.0
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)
    status: str = "completed"
    error_message: Optional[str] = None

    def add_step_result(
        self, 
        kl_div: float, 
        latency: float,
        accumulated_kl: float
    ) -> None:
        """Records the result of a single simulation step."""
        self.per_step_kl.append(kl_div)
        self.per_step_latency.append(latency)
        self.accumulated_kl_divergence = accumulated_kl

    def finalize(self) -> None:
        """Calculates final statistics and marks the run as complete."""
        if self.per_step_latency:
            self.avg_latency = sum(self.per_step_latency) / len(self.per_step_latency)
        self.completed_at = datetime.now()
        self.status = "completed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "total_steps": self.total_steps,
            "method": self.method,
            "accumulated_kl_divergence": self.accumulated_kl_divergence,
            "per_step_kl": self.per_step_kl,
            "per_step_latency": self.per_step_latency,
            "avg_latency": self.avg_latency,
            "config_snapshot": self.config_snapshot,
            "completed_at": self.completed_at.isoformat(),
            "status": self.status,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationRun":
        return cls(
            run_id=data["run_id"],
            seed=data["seed"],
            total_steps=data["total_steps"],
            method=data["method"],
            accumulated_kl_divergence=data.get("accumulated_kl_divergence", 0.0),
            per_step_kl=data.get("per_step_kl", []),
            per_step_latency=data.get("per_step_latency", []),
            avg_latency=data.get("avg_latency", 0.0),
            config_snapshot=data.get("config_snapshot", {}),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else datetime.now(),
            status=data.get("status", "completed"),
            error_message=data.get("error_message")
        )

    def save_to_json(self, path: Union[str, Path]) -> None:
        """Saves the simulation run results to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: Union[str, Path]) -> "SimulationRun":
        """Loads a simulation run from a JSON file."""
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)