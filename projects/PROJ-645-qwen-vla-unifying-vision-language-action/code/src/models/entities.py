"""
Base model entities for the Qwen-VLA Cross-Embodiment Transfer Study.

Defines dataclasses for DatasetSubset, ModelCheckpoint, and EvaluationResult
to ensure consistent data handling across the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json


@dataclass
class DatasetSubset:
    """
    Represents a filtered subset of the Open X-Embodiment dataset.
    
    Attributes:
        name: Unique identifier for the subset (e.g., 'cross_embodiment_filtered')
        source_dataset: Name of the source dataset (e.g., 'open_x_embodiment')
        platforms: List of platform IDs included (e.g., ['franka', 'ur5', 'kuka'])
        row_count: Total number of demonstrations in the subset
        file_path: Path to the saved parquet file
        checksum: SHA256 checksum of the file for reproducibility
        created_at: Timestamp of creation
        metadata: Additional key-value pairs for configuration details
    """
    name: str
    source_dataset: str
    platforms: List[str]
    row_count: int
    file_path: str
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for serialization."""
        return {
            "name": self.name,
            "source_dataset": self.source_dataset,
            "platforms": self.platforms,
            "row_count": self.row_count,
            "file_path": str(self.file_path),
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the entity to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetSubset":
        """Deserialize from a dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class ModelCheckpoint:
    """
    Represents a saved model checkpoint during training.
    
    Attributes:
        epoch: The training epoch number
        step: The global training step number
        file_path: Path to the saved .pt file
        model_state_dict: Path or reference to the state dict (if stored separately)
        optimizer_state_dict: Path or reference to the optimizer state
        metrics: Dictionary of metrics at this checkpoint (e.g., loss, accuracy)
        training_config: Snapshot of hyperparameters used
        created_at: Timestamp of creation
        size_bytes: File size in bytes (for size constraint validation)
    """
    epoch: int
    step: int
    file_path: str
    model_state_dict: Optional[str] = None
    optimizer_state_dict: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    size_bytes: Optional[int] = None

    def validate_size(self, max_size_gb: float = 2.0) -> bool:
        """Check if the checkpoint size is within the allowed limit (default 2GB)."""
        if self.size_bytes is None:
            try:
                self.size_bytes = Path(self.file_path).stat().st_size
            except FileNotFoundError:
                return False
        max_bytes = max_size_gb * (1024 ** 3)
        return self.size_bytes <= max_bytes

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for serialization."""
        return {
            "epoch": self.epoch,
            "step": self.step,
            "file_path": str(self.file_path),
            "model_state_dict": self.model_state_dict,
            "optimizer_state_dict": self.optimizer_state_dict,
            "metrics": self.metrics,
            "training_config": self.training_config,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes
        }

    def to_json(self) -> str:
        """Serialize the entity to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class EvaluationResult:
    """
    Represents the results of a zero-shot evaluation on a benchmark.
    
    Attributes:
        benchmark_name: Name of the benchmark (e.g., 'LIBERO-Spatial')
        embodiment_type: 'within-embodiment' or 'cross-embodiment'
        seed: Random seed used for this evaluation run
        success_rate: Success rate for this specific run (float)
        trajectory_length: Average trajectory length
        metrics: Additional metrics (variance, etc.)
        checkpoint_ref: Reference to the checkpoint used
        created_at: Timestamp of creation
    """
    benchmark_name: str
    embodiment_type: str
    seed: int
    success_rate: float
    trajectory_length: float
    metrics: Dict[str, float] = field(default_factory=dict)
    checkpoint_ref: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for serialization."""
        return {
            "benchmark_name": self.benchmark_name,
            "embodiment_type": self.embodiment_type,
            "seed": self.seed,
            "success_rate": self.success_rate,
            "trajectory_length": self.trajectory_length,
            "metrics": self.metrics,
            "checkpoint_ref": self.checkpoint_ref,
            "created_at": self.created_at.isoformat()
        }

    def to_json(self) -> str:
        """Serialize the entity to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def aggregate_from_list(
        cls, results: List["EvaluationResult"]
    ) -> Dict[str, float]:
        """
        Aggregate a list of EvaluationResults (same benchmark/embodiment)
        into summary statistics: mean, variance, and 95% CI bounds.
        
        Returns a dictionary with keys:
        - mean_success_rate
        - variance
        - ci_95_lower
        - ci_95_upper
        """
        if not results:
            return {}
        
        rates = [r.success_rate for r in results]
        n = len(rates)
        mean_val = sum(rates) / n
        variance = sum((x - mean_val) ** 2 for x in rates) / n if n > 1 else 0.0
        
        # Simple approximation for 95% CI using standard error (assuming normality for aggregation display)
        # Note: Final CI calculation for reporting uses bootstrapping as per spec SC-003
        import math
        std_err = math.sqrt(variance / n) if n > 1 else 0.0
        ci_margin = 1.96 * std_err
        
        return {
            "mean_success_rate": mean_val,
            "variance": variance,
            "ci_95_lower": max(0.0, mean_val - ci_margin),
            "ci_95_upper": min(1.0, mean_val + ci_margin),
            "n_seeds": n
        }