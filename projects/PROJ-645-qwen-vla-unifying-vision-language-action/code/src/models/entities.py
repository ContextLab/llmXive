"""
Base model entities for the Qwen-VLA Cross-Embodiment Transfer Study.

This module defines data structures for:
- DatasetSubset: Metadata describing a filtered dataset partition.
- ModelCheckpoint: Metadata and path information for saved model states.
- EvaluationResult: Structured results from zero-shot evaluation runs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class DatasetSubset:
    """
    Represents a filtered subset of the Open X-Embodiment dataset.

    Attributes:
        name: Human-readable identifier for the subset (e.g., 'open_x_franka_50k').
        source_dataset: Name of the original HuggingFace dataset (e.g., 'open-x-embodiment').
        platform_id: The robot platform identifier (e.g., 'franka', 'ur5', 'kuka').
        row_count: Total number of demonstrations in this subset.
        file_path: Absolute path to the parquet file on disk.
        checksum: SHA256 checksum of the file for integrity verification.
        created_at: Timestamp of creation.
        metadata: Additional key-value metadata (e.g., filter criteria).
    """
    name: str
    source_dataset: str
    platform_id: str
    row_count: int
    file_path: str
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (e.g., to YAML/JSON)."""
        return {
            "name": self.name,
            "source_dataset": self.source_dataset,
            "platform_id": self.platform_id,
            "row_count": self.row_count,
            "file_path": str(self.file_path),
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ModelCheckpoint:
    """
    Represents a saved model checkpoint during training.

    Attributes:
        name: Unique identifier for the checkpoint (e.g., 'epoch_05_franka').
        model_type: Type of model architecture (e.g., 'Qwen2VL-DiT').
        epoch: Training epoch number.
        step: Global training step number.
        file_path: Absolute path to the .pt file.
        size_bytes: File size in bytes.
        hyperparams: Dictionary of hyperparameters used for this run.
        seeds: List of random seeds used for reproducibility.
        created_at: Timestamp of creation.
        metrics: Optional dictionary of metrics at this checkpoint (e.g., loss).
    """
    name: str
    model_type: str
    epoch: int
    step: int
    file_path: str
    size_bytes: int
    hyperparams: Dict[str, Any] = field(default_factory=dict)
    seeds: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "model_type": self.model_type,
            "epoch": self.epoch,
            "step": self.step,
            "file_path": str(self.file_path),
            "size_bytes": self.size_bytes,
            "hyperparams": self.hyperparams,
            "seeds": self.seeds,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
        }

    @property
    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Return size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)


@dataclass
class EvaluationResult:
    """
    Represents the results of a zero-shot evaluation run.

    Attributes:
        task_name: Name of the evaluation benchmark (e.g., 'LIBERO-Spatial').
        embodiment_type: 'within-embodiment' or 'cross-embodiment'.
        platform_id: The robot platform tested.
        success_rate: List of success rates per seed.
        trajectory_length: Average trajectory length.
        variance: Variance of the success rates.
        ci_95_lower: Lower bound of the 95% confidence interval.
        ci_95_upper: Upper bound of the 95% confidence interval.
        seeds: List of random seeds used for this evaluation.
        checkpoint_name: Name of the model checkpoint evaluated.
        created_at: Timestamp of creation.
        additional_metrics: Dictionary for any other metrics.
    """
    task_name: str
    embodiment_type: str
    platform_id: str
    success_rate: List[float]
    trajectory_length: float
    variance: float
    ci_95_lower: float
    ci_95_upper: float
    seeds: List[int]
    checkpoint_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_name": self.task_name,
            "embodiment_type": self.embodiment_type,
            "platform_id": self.platform_id,
            "success_rate": self.success_rate,
            "trajectory_length": self.trajectory_length,
            "variance": self.variance,
            "ci_95_lower": self.ci_95_lower,
            "ci_95_upper": self.ci_95_upper,
            "seeds": self.seeds,
            "checkpoint_name": self.checkpoint_name,
            "created_at": self.created_at.isoformat(),
            "additional_metrics": self.additional_metrics,
        }

    @property
    def mean_success_rate(self) -> float:
        """Calculate mean success rate across seeds."""
        if not self.success_rate:
            return 0.0
        return sum(self.success_rate) / len(self.success_rate)