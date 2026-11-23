"""
Training callbacks for logging metrics during the experiment.

Implements LoggingCallback to track epoch, train_loss, val_loss, gap, time, ram, and seed_id.
"""
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from project utils
from utils.monitor import get_ram_usage_gb, get_elapsed_time, get_resource_snapshot
from utils.logging import get_logger, info, error, warning

class TrainingMetrics:
    """Container for aggregated training metrics."""
    def __init__(self):
        self.epoch: int = 0
        self.train_loss: float = 0.0
        self.val_loss: float = 0.0
        self.gap: float = 0.0
        self.time_elapsed: float = 0.0
        self.ram_usage_gb: float = 0.0
        self.seed_id: int = 0
        self.model_type: str = ""
        self.timestamp: str = ""

class LoggingCallback:
    """
    Callback to log training metrics to CSV and console.
    
    Logs: epoch, train_loss, val_loss, gap, time, ram, seed_id.
    """
    def __init__(self, log_file_path: Path, seed_id: int, model_type: str = "unknown"):
        self.log_file_path = log_file_path
        self.seed_id = seed_id
        self.model_type = model_type
        self.logger = get_logger("TrainingCallback")
        self.start_time: Optional[float] = None
        self.epoch_start_time: Optional[float] = None
        self.headers_written = False
        
        # Ensure directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV file if it doesn't exist
        if not self.log_file_path.exists():
            with open(self.log_file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'seed_id', 'model_type', 'epoch', 
                    'train_loss', 'val_loss', 'gap', 'time_elapsed_s', 'ram_usage_gb'
                ])

    def on_train_start(self):
        """Called at the beginning of training."""
        self.start_time = time.time()
        info(self.logger, f"Training started for seed_id={self.seed_id}, model={self.model_type}")

    def on_epoch_start(self, epoch: int):
        """Called at the beginning of each epoch."""
        self.epoch_start_time = time.time()
        self.logger.debug(f"Epoch {epoch} starting...")

    def on_epoch_end(self, epoch: int, train_loss: float, val_loss: float):
        """
        Called at the end of each epoch.
        
        Args:
            epoch: Current epoch number (0-indexed or 1-indexed)
            train_loss: Average training loss for the epoch
            val_loss: Average validation loss for the epoch
        """
        if self.epoch_start_time is None:
            error(self.logger, "on_epoch_end called without on_epoch_start")
            return

        # Calculate metrics
        epoch_time = time.time() - self.epoch_start_time
        total_time = time.time() - self.start_time if self.start_time else 0.0
        ram_gb = get_ram_usage_gb()
        gap = val_loss - train_loss
        
        # Create metrics record
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'seed_id': self.seed_id,
            'model_type': self.model_type,
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'gap': gap,
            'time_elapsed_s': total_time,
            'ram_usage_gb': ram_gb
        }

        # Log to CSV
        self._write_to_csv(metrics)
        
        # Log to console
        self._log_to_console(metrics, epoch_time)

        self.epoch_start_time = None

    def _write_to_csv(self, metrics: Dict[str, Any]):
        """Append metrics to the CSV log file."""
        try:
            with open(self.log_file_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'seed_id', 'model_type', 'epoch', 
                    'train_loss', 'val_loss', 'gap', 'time_elapsed_s', 'ram_usage_gb'
                ])
                writer.writerow(metrics)
        except Exception as e:
            error(self.logger, f"Failed to write metrics to CSV: {e}")

    def _log_to_console(self, metrics: Dict[str, Any], epoch_time: float):
        """Log metrics to the console."""
        log_msg = (
            f"[Seed {self.seed_id}] Epoch {metrics['epoch']} | "
            f"Train Loss: {metrics['train_loss']:.4f} | "
            f"Val Loss: {metrics['val_loss']:.4f} | "
            f"Gap: {metrics['gap']:.4f} | "
            f"Time: {epoch_time:.2f}s | "
            f"RAM: {metrics['ram_usage_gb']:.2f}GB"
        )
        info(self.logger, log_msg)

    def on_train_end(self):
        """Called at the end of training."""
        total_time = time.time() - self.start_time if self.start_time else 0.0
        info(self.logger, f"Training completed for seed_id={self.seed_id}. Total time: {total_time:.2f}s")

def create_logging_callback(
    log_dir: Path, 
    seed_id: int, 
    model_type: str = "unknown", 
    filename: str = "training_logs.csv"
) -> LoggingCallback:
    """
    Factory function to create a LoggingCallback instance.
    
    Args:
        log_dir: Directory to save the log file
        seed_id: The seed ID for this run
        model_type: Type of model (e.g., 'autoregressive', 'diffusion')
        filename: Name of the log file
        
    Returns:
        Configured LoggingCallback instance
    """
    log_file_path = log_dir / filename
    return LoggingCallback(log_file_path, seed_id, model_type)