"""
Training Monitor for Symbolic-Guava LLM Fine-tuning.

Implements monitoring logic to track loss decrease (target: >=15% in 4h),
logging metrics to data/artifacts/training_metrics.json.
"""
import json
import os
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project configuration and utilities
from utils.config import get_path, get_hyperparameter
from utils.exceptions import LlmXiveError
from utils.environment_config import verify_cpu_only_constraint

# Constants
TRAINING_METRICS_FILE = "data/artifacts/training_metrics.json"
TARGET_LOSS_DECREASE_PERCENT = 15.0
MAX_TRAINING_HOURS = 4.0

class TrainingMonitor:
    """
    Monitors LLM training progress, tracking loss decrease and logging metrics.
    """
    
    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize the training monitor.
        
        Args:
            output_path: Path to the metrics JSON file. Defaults to project config.
        """
        self.output_path = output_path or get_path(TRAINING_METRICS_FILE)
        self.metrics: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.initial_loss: Optional[float] = None
        self.current_loss: Optional[float] = None
        self.epoch_count: int = 0
        
        # Ensure output directory exists
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Verify CPU constraint if not using GPU escape hatch
        verify_cpu_only_constraint()
    
    def start_training(self) -> None:
        """Record the start of training."""
        self.start_time = time.time()
        self.epoch_count = 0
        self.metrics = []
        self._save_metrics()
    
    def record_epoch(self, epoch: int, loss: float) -> None:
        """
        Record metrics for a training epoch.
        
        Args:
            epoch: Epoch number (0-indexed or 1-indexed).
            loss: Loss value for this epoch.
        """
        if self.start_time is None:
            raise LlmXiveError("Training has not started. Call start_training() first.")
        
        self.epoch_count = epoch
        self.current_loss = loss
        
        if self.initial_loss is None:
            self.initial_loss = loss
        
        timestamp = time.time()
        elapsed_hours = (timestamp - self.start_time) / 3600.0
        
        # Calculate loss decrease percentage
        loss_decrease_pct = 0.0
        if self.initial_loss > 0:
            loss_decrease_pct = ((self.initial_loss - loss) / self.initial_loss) * 100.0
        
        metric_entry = {
            "epoch": epoch,
            "loss": loss,
            "timestamp": timestamp,
            "elapsed_hours": round(elapsed_hours, 4),
            "loss_decrease_percent": round(loss_decrease_pct, 4),
            "target_met": loss_decrease_pct >= TARGET_LOSS_DECREASE_PERCENT
        }
        
        self.metrics.append(metric_entry)
        self._save_metrics()
    
    def check_target_achieved(self) -> bool:
        """
        Check if the target loss decrease (>=15%) has been achieved.
        
        Returns:
            True if target is met, False otherwise.
        """
        if self.current_loss is None or self.initial_loss is None:
            return False
        
        if self.initial_loss <= 0:
            return False
        
        decrease_pct = ((self.initial_loss - self.current_loss) / self.initial_loss) * 100.0
        return decrease_pct >= TARGET_LOSS_DECREASE_PERCENT
    
    def check_time_limit(self) -> bool:
        """
        Check if training has exceeded the time limit (4 hours).
        
        Returns:
            True if time limit exceeded, False otherwise.
        """
        if self.start_time is None:
            return False
        
        elapsed_hours = (time.time() - self.start_time) / 3600.0
        return elapsed_hours >= MAX_TRAINING_HOURS
    
    def get_training_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the training run.
        
        Returns:
            Dictionary containing training summary statistics.
        """
        if not self.metrics:
            return {
                "status": "no_data",
                "message": "No training metrics recorded."
            }
        
        final_epoch = self.metrics[-1]["epoch"]
        final_loss = self.metrics[-1]["loss"]
        initial_loss = self.initial_loss or final_loss
        
        loss_decrease_pct = 0.0
        if initial_loss > 0:
            loss_decrease_pct = ((initial_loss - final_loss) / initial_loss) * 100.0
        
        elapsed_hours = (time.time() - self.start_time) / 3600.0 if self.start_time else 0.0
        
        return {
            "status": "completed" if self.check_target_achieved() else "incomplete",
            "target_loss_decrease_percent": TARGET_LOSS_DECREASE_PERCENT,
            "actual_loss_decrease_percent": round(loss_decrease_pct, 4),
            "target_met": self.check_target_achieved(),
            "time_limit_hours": MAX_TRAINING_HOURS,
            "elapsed_hours": round(elapsed_hours, 4),
            "time_limit_exceeded": self.check_time_limit(),
            "total_epochs": final_epoch + 1,
            "initial_loss": round(initial_loss, 6),
            "final_loss": round(final_loss, 6),
            "metrics_file": self.output_path
        }
    
    def _save_metrics(self) -> None:
        """Save current metrics to the output JSON file."""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)
    
    def close(self) -> Dict[str, Any]:
        """
        Finalize training monitoring and return summary.
        
        Returns:
            Training summary dictionary.
        """
        summary = self.get_training_summary()
        
        # Append summary to metrics file for reference
        with open(self.output_path, 'a', encoding='utf-8') as f:
            f.write("\n")
            json.dump({"summary": summary}, f, indent=2)
        
        return summary


def run_training_monitoring_demo() -> None:
    """
    Demo function to simulate training monitoring.
    This demonstrates the monitor's functionality with simulated data.
    """
    monitor = TrainingMonitor()
    monitor.start_training()
    
    # Simulate training epochs with decreasing loss
    simulated_losses = [2.5, 2.2, 1.9, 1.6, 1.3, 1.0, 0.8, 0.6, 0.5, 0.4]
    
    print("Starting training monitoring demo...")
    print(f"Target: {TARGET_LOSS_DECREASE_PERCENT}% loss decrease")
    print(f"Time limit: {MAX_TRAINING_HOURS} hours\n")
    
    for epoch, loss in enumerate(simulated_losses):
        monitor.record_epoch(epoch, loss)
        
        status = "TARGET MET" if monitor.check_target_achieved() else "In Progress"
        if monitor.check_time_limit():
            status = "TIME LIMIT EXCEEDED"
        
        print(f"Epoch {epoch}: Loss={loss:.4f} [{status}]")
        
        if monitor.check_target_achieved():
            print("\nTarget achieved! Stopping training.")
            break
        
        if monitor.check_time_limit():
            print("\nTime limit exceeded! Triggering GPU escape hatch.")
            break
    
    summary = monitor.close()
    print(f"\nTraining Summary:")
    print(json.dumps(summary, indent=2))


def main() -> None:
    """
    Main entry point for the training monitor script.
    """
    parser = argparse.ArgumentParser(description="Training Monitor for Symbolic-Guava LLM")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with simulated data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output metrics file"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        run_training_monitoring_demo()
    else:
        print("Training monitor initialized. Use this module within train_llm.py to monitor training.")
        print("Run with --demo flag to see a demonstration.")


if __name__ == "__main__":
    main()