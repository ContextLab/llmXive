import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logging import get_logger, info, error, warning
from utils.monitor import get_ram_usage_gb, get_elapsed_time, get_resource_snapshot

logger = get_logger(__name__)


class TrainingMetrics:
    """Container for metrics logged during a training epoch."""

    def __init__(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float,
        seed_id: int,
        model_type: str = "unknown",
    ):
        self.epoch = epoch
        self.train_loss = train_loss
        self.val_loss = val_loss
        self.gap = train_loss - val_loss
        self.seed_id = seed_id
        self.model_type = model_type
        self.timestamp = datetime.now().isoformat()
        self.ram_gb: Optional[float] = None
        self.wall_time_seconds: float = 0.0
        self.peak_ram_gb: Optional[float] = None
        self.resource_snapshot: Dict[str, Any] = {}

    def record_resources(self, start_time: float, end_time: Optional[float] = None):
        """Record RAM usage and wall-clock time for the epoch."""
        if end_time is None:
            end_time = time.time()
        self.wall_time_seconds = end_time - start_time
        
        # Get current RAM usage
        self.ram_gb = get_ram_usage_gb()
        
        # Get full resource snapshot to track peak memory
        snapshot = get_resource_snapshot()
        self.resource_snapshot = snapshot
        
        # Track peak RAM if available in snapshot
        if 'peak_rss' in snapshot:
            self.peak_ram_gb = snapshot['peak_rss'] / (1024 * 1024 * 1024)  # Convert to GB
        elif self.ram_gb is not None:
            # Fallback: use current as peak if peak tracking not available
            self.peak_ram_gb = self.ram_gb

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary for logging/CSV export."""
        return {
            "epoch": self.epoch,
            "train_loss": self.train_loss,
            "val_loss": self.val_loss,
            "gap": self.gap,
            "time": self.wall_time_seconds,
            "ram": self.ram_gb,
            "peak_ram": self.peak_ram_gb,
            "seed_id": self.seed_id,
            "model_type": self.model_type,
            "timestamp": self.timestamp,
            "cpu_percent": self.resource_snapshot.get('cpu_percent', 0.0),
            "num_threads": self.resource_snapshot.get('num_threads', 0),
        }


class LoggingCallback:
    """
    Callback to log training metrics to CSV and console.

    Logs: epoch, train_loss, val_loss, gap, time, ram, peak_ram, seed_id, model_type.
    """

    def __init__(
        self,
        log_file_path: Path,
        seed_id: int,
        model_type: str = "unknown",
        header_written: Optional[bool] = None,
    ):
        self.log_file_path = log_file_path
        self.seed_id = seed_id
        self.model_type = model_type
        self.header_written = header_written
        self.metrics_history: List[TrainingMetrics] = []
        self.epoch_start_time: Optional[float] = None

        # Ensure directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize CSV file if it doesn't exist or header not written
        if not self.log_file_path.exists() or header_written is False:
            self._write_header()
            self.header_written = True

    def _write_header(self):
        """Write CSV header to the log file."""
        fieldnames = [
            "epoch",
            "train_loss",
            "val_loss",
            "gap",
            "time",
            "ram",
            "peak_ram",
            "seed_id",
            "model_type",
            "timestamp",
            "cpu_percent",
            "num_threads",
        ]
        with open(self.log_file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        logger.info(f"Initialized training log file: {self.log_file_path}")

    def on_epoch_start(self):
        """Called at the start of an epoch to record start time."""
        self.epoch_start_time = time.time()
        logger.debug(f"[Seed {self.seed_id} {self.model_type}] Epoch start recorded")

    def on_epoch_end(self, epoch: int, train_loss: float, val_loss: float, start_time: float):
        """
        Called at the end of an epoch to record metrics.

        Args:
            epoch: Current epoch number (0-indexed or 1-indexed, logged as-is).
            train_loss: Training loss for the epoch.
            val_loss: Validation loss for the epoch.
            start_time: Timestamp when the epoch started (for time calculation).
        """
        metrics = TrainingMetrics(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            seed_id=self.seed_id,
            model_type=self.model_type,
        )
        metrics.record_resources(start_time)
        self.metrics_history.append(metrics)

        # Append to CSV
        with open(self.log_file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=metrics.to_dict().keys())
            writer.writerow(metrics.to_dict())

        # Log to console with peak memory
        info(
            f"[Seed {self.seed_id} {self.model_type}] Epoch {epoch}: "
            f"train_loss={metrics.train_loss:.4f}, "
            f"val_loss={metrics.val_loss:.4f}, "
            f"gap={metrics.gap:.4f}, "
            f"time={metrics.wall_time_seconds:.2f}s, "
            f"ram={metrics.ram_gb:.2f}GB, "
            f"peak_ram={metrics.peak_ram_gb:.2f}GB"
        )

    def get_logs(self) -> List[Dict[str, Any]]:
        """Return the list of all logged metrics dictionaries."""
        return [m.to_dict() for m in self.metrics_history]

    def get_peak_memory_gb(self) -> Optional[float]:
        """Return the peak RAM observed across all epochs."""
        peak_rams = [m.peak_ram_gb for m in self.metrics_history if m.peak_ram_gb is not None]
        return max(peak_rams) if peak_rams else None


def create_logging_callback(
    log_dir: Path,
    seed_id: int,
    model_type: str,
) -> LoggingCallback:
    """
    Factory function to create a LoggingCallback instance.

    Args:
        log_dir: Directory where the CSV log file will be saved.
        seed_id: Unique identifier for the current training run (seed).
        model_type: Type of model being trained (e.g., 'autoregressive', 'diffusion').

    Returns:
        Configured LoggingCallback instance.
    """
    log_file_path = log_dir / f"training_log_seed_{seed_id}_{model_type}.csv"
    return LoggingCallback(
        log_file_path=log_file_path,
        seed_id=seed_id,
        model_type=model_type,
    )