"""
Training Runner with Hard Wall-Clock Time Limit Enforcement (Watchdog).

Implements FR-004: Hard wall-clock time limit enforcement to prevent
training runs from exceeding the configured budget.
"""
import json
import os
import sys
import time
import signal
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# Import from project utilities
try:
    from utils.logging import get_logger, log_with_context, log_error
    from utils.constants import ErrorCodes
except ImportError:
    # Fallback for direct execution in some environments
    import logging
    logger = logging.getLogger(__name__)
    def get_logger(name): return logging.getLogger(name)
    def log_with_context(msg, ctx=None): logger.info(msg)
    def log_error(msg, exc=None): logger.error(msg, exc_info=exc)
    
    class ErrorCodes:
        TIMEOUT_EXCEEDED = "TIMEOUT_EXCEEDED"
        RUNTIME_ERROR = "RUNTIME_ERROR"
        CONFIG_ERROR = "CONFIG_ERROR"

logger = get_logger(__name__)

class TrainingTimeoutError(Exception):
    """Raised when the training run exceeds the wall-clock time limit."""
    def __init__(self, message: str, elapsed_seconds: float, limit_seconds: float):
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds
        self.limit_seconds = limit_seconds
        self.code = ErrorCodes.TIMEOUT_EXCEEDED

class MockModel:
    """
    Mock model for testing the training pipeline.
    In production, this would be a real LLM or policy network.
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.training_logs = []
        self.is_trained = False

    def train_step(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a training step."""
        # Simulate computation time
        time.sleep(0.1)
        return {
            "loss": 0.5,
            "success_rate": 0.6,
            "steps": 1
        }

    def save_checkpoint(self, path: Path):
        """Save model checkpoint."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"status": "mock_checkpoint"}, f)

    def load_checkpoint(self, path: Path):
        """Load model checkpoint."""
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return None

class TrainingRunner:
    """
    Training runner with hard wall-clock time limit enforcement.
    
    Implements FR-004: Hard wall-clock time limit enforcement (watchdog).
    The runner will terminate the training process if it exceeds the
    configured time budget, ensuring reproducibility and resource control.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: Path,
        model: Optional[MockModel] = None
    ):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = model or MockModel(config)
        
        # Time limit configuration
        self.time_limit_seconds = config.get('time_limit_seconds', 3600)
        self.start_time: Optional[float] = None
        self.elapsed_time: float = 0.0
        
        # Logging setup
        self.log_file = self.output_dir / "training_log.json"
        self.trace_file = self.output_dir / "scheduler_trace.json"
        
        # Initialize log file
        self._init_log_file()
        
        logger.info(f"TrainingRunner initialized with {self.time_limit_seconds}s time limit")
        log_with_context("TrainingRunner initialized", {
            "time_limit_seconds": self.time_limit_seconds,
            "output_dir": str(self.output_dir)
        })

    def _init_log_file(self):
        """Initialize the training log file with schema."""
        log_data = {
            "schema_version": "1.0",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "config": self.config,
            "events": []
        }
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

    def _check_time_limit(self) -> bool:
        """
        Check if the training run has exceeded the time limit.
        
        Returns:
            bool: True if within limits, False if exceeded.
        
        Raises:
            TrainingTimeoutError: If the time limit is exceeded.
        """
        if self.start_time is None:
            return True
        
        self.elapsed_time = time.time() - self.start_time
        
        if self.elapsed_time >= self.time_limit_seconds:
            raise TrainingTimeoutError(
                f"Training run exceeded time limit: {self.elapsed_time:.2f}s >= {self.time_limit_seconds}s",
                elapsed_seconds=self.elapsed_time,
                limit_seconds=self.time_limit_seconds
            )
        
        return True

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event to the training log file."""
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "data": data
            }
            log_data["events"].append(event)
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            log_error("Failed to log event", e)

    def run_training(
        self,
        task_batches: List[Dict[str, Any]],
        max_steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the training loop with hard time limit enforcement.
        
        Args:
            task_batches: List of task batches to process
            max_steps: Optional maximum number of steps (in addition to time limit)
        
        Returns:
            Dict containing training results and metadata
        
        Raises:
            TrainingTimeoutError: If the training exceeds the time limit
        """
        self.start_time = time.time()
        results = {
            "status": "running",
            "steps_completed": 0,
            "total_loss": 0.0,
            "average_success_rate": 0.0,
            "time_limit_seconds": self.time_limit_seconds,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat()
        }
        
        self._log_event("training_start", {
            "time_limit_seconds": self.time_limit_seconds,
            "num_batches": len(task_batches)
        })
        
        try:
            for batch_idx, batch in enumerate(task_batches):
                # Check time limit before each batch
                self._check_time_limit()
                
                # Log batch start
                self._log_event("batch_start", {
                    "batch_idx": batch_idx,
                    "batch_size": len(batch.get("tasks", []))
                })
                
                # Process batch
                batch_results = []
                for task in batch.get("tasks", []):
                    # Check time limit for each task
                    self._check_time_limit()
                    
                    # Simulate training step
                    step_result = self.model.train_step(task)
                    batch_results.append(step_result)
                    
                    # Update results
                    results["steps_completed"] += 1
                    results["total_loss"] += step_result.get("loss", 0.0)
                    
                    if max_steps and results["steps_completed"] >= max_steps:
                        break
                
                # Log batch completion
                self._log_event("batch_complete", {
                    "batch_idx": batch_idx,
                    "num_tasks": len(batch_results),
                    "average_loss": sum(r.get("loss", 0.0) for r in batch_results) / len(batch_results) if batch_results else 0.0
                })
                
                if max_steps and results["steps_completed"] >= max_steps:
                    break
            
            # Training completed successfully
            results["status"] = "completed"
            results["end_time"] = datetime.now(timezone.utc).isoformat()
            results["total_time_seconds"] = time.time() - self.start_time
            results["average_success_rate"] = (
                sum(r.get("success_rate", 0.0) for r in batch_results) / len(batch_results)
                if batch_results else 0.0
            )
            
            self._log_event("training_complete", {
                "status": "completed",
                "total_steps": results["steps_completed"],
                "total_time_seconds": results["total_time_seconds"]
            })
            
        except TrainingTimeoutError as e:
            results["status"] = "timeout"
            results["error"] = str(e)
            results["elapsed_seconds"] = e.elapsed_seconds
            results["end_time"] = datetime.now(timezone.utc).isoformat()
            
            self._log_event("training_timeout", {
                "elapsed_seconds": e.elapsed_seconds,
                "limit_seconds": e.limit_seconds
            })
            
            log_error(f"Training timeout: {e}")
            raise
        
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["end_time"] = datetime.now(timezone.utc).isoformat()
            
            self._log_event("training_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            log_error(f"Training error: {e}")
            raise
        
        return results

    def save_results(self, results: Dict[str, Any]):
        """Save training results to output directory."""
        results_file = self.output_dir / "training_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self._log_event("results_saved", {
            "results_file": str(results_file)
        })
        
        logger.info(f"Training results saved to {results_file}")

def main():
    """
    Main entry point for the training runner.
    
    This demonstrates the hard time limit enforcement by running
    a training loop that will terminate if it exceeds the configured
    time budget.
    """
    # Configuration
    config = {
        "model_name": "Qwen3-VL-4B-Instruct",
        "time_limit_seconds": 300,  # 5 minutes
        "batch_size": 10,
        "max_steps": 100
    }
    
    output_dir = Path("data/processed/training_run_001")
    
    # Create mock task batches
    task_batches = []
    for i in range(20):
        task_batches.append({
            "batch_id": f"batch_{i}",
            "tasks": [
                {"task_id": f"task_{j}", "difficulty": 0.5 + j * 0.05}
                for j in range(5)
            ]
        })
    
    # Initialize runner
    runner = TrainingRunner(config, output_dir)
    
    try:
        # Run training
        results = runner.run_training(task_batches, max_steps=config["max_steps"])
        
        # Save results
        runner.save_results(results)
        
        print(f"Training completed: {results['status']}")
        print(f"Steps completed: {results['steps_completed']}")
        print(f"Total time: {results.get('total_time_seconds', 0):.2f}s")
        
        if results["status"] == "timeout":
            print(f"TIMEOUT: Exceeded {results['limit_seconds']}s limit")
            sys.exit(1)
        
    except TrainingTimeoutError as e:
        print(f"TIMEOUT: Training exceeded time limit ({e.elapsed_seconds:.2f}s >= {e.limit_seconds}s)")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()