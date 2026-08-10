"""
Training callbacks for logging and monitoring during model training.
"""
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from utils.logging import get_logger, info, error, warning
from utils.monitor import get_ram_usage_gb, get_elapsed_time, get_resource_snapshot

logger = get_logger(__name__)

@dataclass
class TrainingMetrics:
    """Container for training metrics at a given step/epoch."""
    epoch: int
    step: int
    train_loss: Optional[float] = None
    val_loss: Optional[float] = None
    gap: Optional[float] = None
    time_elapsed: float = 0.0
    ram_usage_gb: float = 0.0
    seed_id: Optional[int] = None
    status: str = "RUNNING"  # RUNNING, TRUNCATED, COMPLETED

class LoggingCallback:
    """
    Callback to log training metrics to CSV and console.
    """
    def __init__(self, log_path: Path, seed_id: int):
        self.log_path = log_path
        self.seed_id = seed_id
        self.start_time = time.time()
        self.metrics_history: List[TrainingMetrics] = []
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not self.log_path.exists():
            self._initialize_csv()
        
        info(f"LoggingCallback initialized for seed {seed_id}, log path: {self.log_path}")

    def _initialize_csv(self):
        """Initialize the CSV log file with headers."""
        with open(self.log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'seed_id', 'epoch', 'step', 
                'train_loss', 'val_loss', 'gap', 
                'time_elapsed', 'ram_usage_gb', 'status'
            ])

    def on_epoch_start(self, epoch: int):
        """Called at the beginning of an epoch."""
        info(f"[Seed {self.seed_id}] Epoch {epoch} starting...")

    def on_epoch_end(self, epoch: int, train_loss: float, val_loss: float):
        """Called at the end of an epoch."""
        elapsed = time.time() - self.start_time
        ram = get_ram_usage_gb()
        gap = val_loss - train_loss if val_loss is not None else None
        
        metrics = TrainingMetrics(
            epoch=epoch,
            step=epoch,  # Simplified step tracking
            train_loss=train_loss,
            val_loss=val_loss,
            gap=gap,
            time_elapsed=elapsed,
            ram_usage_gb=ram,
            seed_id=self.seed_id,
            status="RUNNING"
        )
        
        self.metrics_history.append(metrics)
        self._write_to_csv(metrics)
        
        info(
            f"[Seed {self.seed_id}] Epoch {epoch} complete - "
            f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
            f"Gap: {gap:.4f if gap else 'N/A':.4f}, "
            f"Time: {elapsed:.2f}s, RAM: {ram:.2f}GB"
        )

    def on_training_end(self, status: str = "COMPLETED"):
        """Called when training finishes."""
        for metrics in self.metrics_history:
            if metrics.epoch == self.metrics_history[-1].epoch:
                metrics.status = status
                # Update the last entry in CSV
                self._update_last_row(metrics)
        
        info(f"[Seed {self.seed_id}] Training finished with status: {status}")

    def _write_to_csv(self, metrics: TrainingMetrics):
        """Append metrics to the CSV log file."""
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                metrics.seed_id,
                metrics.epoch,
                metrics.step,
                metrics.train_loss,
                metrics.val_loss,
                metrics.gap,
                metrics.time_elapsed,
                metrics.ram_usage_gb,
                metrics.status
            ])

    def _update_last_row(self, metrics: TrainingMetrics):
        """Update the last row in the CSV with final status."""
        # Read all rows
        rows = []
        with open(self.log_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) > 1:  # Skip header
            # Update the last data row
            rows[-1][-1] = metrics.status  # Update status column
        
        # Write back
        with open(self.log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

def create_logging_callback(log_dir: Path, seed_id: int) -> LoggingCallback:
    """
    Factory function to create a LoggingCallback instance.
    
    Args:
        log_dir: Directory where logs will be saved.
        seed_id: Identifier for the current training seed.
        
    Returns:
        Configured LoggingCallback instance.
    """
    log_path = log_dir / f"training_log_seed_{seed_id}.csv"
    return LoggingCallback(log_path, seed_id)
