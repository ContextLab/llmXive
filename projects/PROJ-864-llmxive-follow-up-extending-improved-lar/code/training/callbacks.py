"""
Training callbacks for logging metrics: epoch, train_loss, val_loss, gap, time, ram.

This module provides the LoggingCallback class which is used within the training loop
to record metrics at the end of each epoch. It integrates with the project's
configuration, logging, and monitoring utilities.

Output:
    Writes metrics to `data/artifacts/training_logs.csv` (or the configured artifacts path).
"""
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch

# Import project utilities
from utils.config import get_artifacts_dir, get_config, ConfigError
from utils.logging import get_logger, info, debug
from utils.monitor import get_ram_usage_gb, get_elapsed_time

logger = get_logger(__name__)


class TrainingMetrics:
    """Container for metrics accumulated during a training session."""
    
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.session_start_time: Optional[float] = None
    
    def reset(self):
        """Reset metrics for a new session."""
        self.rows = []
        self.start_time = None
        self.session_start_time = time.time()
    
    def record_epoch(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float,
        ram_gb: float,
        elapsed_time_seconds: float
    ):
        """Record a single epoch's metrics."""
        gap = train_loss - val_loss
        
        row = {
            "timestamp": datetime.now().isoformat(),
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "gap": gap,
            "elapsed_time_seconds": elapsed_time_seconds,
            "ram_gb": ram_gb
        }
        self.rows.append(row)
        return row
    
    def save_to_csv(self, filepath: Optional[Path] = None):
        """Save accumulated metrics to a CSV file."""
        if not self.rows:
            logger.warning("No metrics to save.")
            return
        
        if filepath is None:
            artifacts_dir = get_artifacts_dir()
            filepath = artifacts_dir / "training_logs.csv"
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "timestamp", "epoch", "train_loss", "val_loss", 
            "gap", "elapsed_time_seconds", "ram_gb"
        ]
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)
        
        info(f"Training metrics saved to {filepath}")


class LoggingCallback:
    """
    Callback to log training metrics (epoch, loss, gap, time, RAM) to console and file.
    
    This callback is designed to be used within the `train_loop` in `training/train_loop.py`.
    It accumulates metrics and writes them to a CSV file at the end of training or
    periodically.
    """
    
    def __init__(self, log_interval: int = 1):
        """
        Initialize the logging callback.
        
        Args:
            log_interval: Log to console every N epochs.
        """
        self.log_interval = log_interval
        self.metrics = TrainingMetrics()
        self.metrics.start_time = time.time()
        self.metrics.session_start_time = time.time()
    
    def on_epoch_end(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float
    ):
        """
        Called at the end of an epoch to log metrics.
        
        Args:
            epoch: Current epoch number (1-based).
            train_loss: Average training loss for the epoch.
            val_loss: Average validation loss for the epoch.
        """
        # Get resource metrics
        ram_gb = get_ram_usage_gb()
        elapsed = time.time() - self.metrics.start_time
        
        # Record metrics
        row = self.metrics.record_epoch(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            ram_gb=ram_gb,
            elapsed_time_seconds=elapsed
        )
        
        # Log to console if interval matches
        if epoch % self.log_interval == 0:
            info(
                f"Epoch {epoch}: "
                f"train_loss={train_loss:.4f}, "
                f"val_loss={val_loss:.4f}, "
                f"gap={row['gap']:.4f}, "
                f"time={elapsed:.1f}s, "
                f"ram={ram_gb:.2f}GB"
            )
        else:
            debug(
                f"Epoch {epoch}: "
                f"train_loss={train_loss:.4f}, "
                f"val_loss={val_loss:.4f}"
            )
    
    def on_train_end(self, filepath: Optional[Path] = None):
        """
        Called at the end of training to finalize logs.
        
        Args:
            filepath: Optional path to save the CSV. If None, uses config default.
        """
        # Final RAM check
        final_ram = get_ram_usage_gb()
        total_time = time.time() - (self.metrics.session_start_time or time.time())
        
        info(
            f"Training complete. "
            f"Total time: {total_time:.1f}s, "
            f"Final RAM: {final_ram:.2f}GB"
        )
        
        # Save to CSV
        self.metrics.save_to_csv(filepath)
    
    def reset(self):
        """Reset the callback state for a new training run."""
        self.metrics.reset()
        self.metrics.start_time = time.time()
        self.metrics.session_start_time = time.time()


# Convenience function to create a callback instance
def create_logging_callback(log_interval: int = 1) -> LoggingCallback:
    """
    Factory function to create a LoggingCallback instance.
    
    Args:
        log_interval: Log to console every N epochs.
    
    Returns:
        A configured LoggingCallback instance.
    """
    return LoggingCallback(log_interval=log_interval)