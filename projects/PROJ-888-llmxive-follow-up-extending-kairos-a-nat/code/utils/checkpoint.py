import os
import sys
import time
import json
import logging
import signal
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from utils.logging import get_logger, ResourceLimitExceeded
from utils.monitor import ResourceMonitor, get_elapsed_time, format_duration, format_bytes

logger = get_logger(__name__)

# Default limits
DEFAULT_MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
DEFAULT_CHECKPOINT_INTERVAL_SECONDS = 300  # 5 minutes
DEFAULT_CHECKPOINT_DIR = "state/checkpoints"

@dataclass
class CheckpointState:
    """Holds the serializable state required to resume a process."""
    start_time: float
    last_checkpoint_time: float
    iteration: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    extra_data: Dict[str, Any] = field(default_factory=dict)

class CheckpointManager:
    """
    Manages periodic checkpointing and graceful exit based on a maximum runtime limit.
    
    This class handles:
    1. Recording start time and tracking elapsed time.
    2. Periodically saving state to disk.
    3. Checking against a hard time limit and raising an exception if exceeded.
    4. Handling SIGTERM/SIGINT to trigger a final checkpoint before exit.
    """
    
    def __init__(
        self,
        checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR,
        max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
        checkpoint_interval_seconds: int = DEFAULT_CHECKPOINT_INTERVAL_SECONDS,
        checkpoint_prefix: str = "checkpoint"
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_runtime_seconds = max_runtime_seconds
        self.checkpoint_interval_seconds = checkpoint_interval_seconds
        self.checkpoint_prefix = checkpoint_prefix
        
        self.start_time: Optional[float] = None
        self.last_checkpoint_time: Optional[float] = None
        self.current_iteration: int = 0
        self.state: Optional[CheckpointState] = None
        self._lock = threading.Lock()
        self._shutdown_requested = False
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown signals."""
        logger.warning(f"Received signal {signum}. Initiating graceful shutdown...")
        self._shutdown_requested = True
        # Attempt one final checkpoint
        if self.state:
            self.save_checkpoint()

    def start(self, initial_metrics: Optional[Dict[str, Any]] = None):
        """Initialize the checkpoint manager and record start time."""
        if self.start_time is not None:
            logger.warning("Checkpoint manager already started.")
            return
        
        self.start_time = time.time()
        self.last_checkpoint_time = self.start_time
        self.state = CheckpointState(
            start_time=self.start_time,
            last_checkpoint_time=self.start_time,
            iteration=0,
            metrics=initial_metrics or {}
        )
        logger.info(f"Checkpoint manager started. Max runtime: {format_duration(self.max_runtime_seconds)}")
        logger.info(f"Checkpoint directory: {self.checkpoint_dir}")

    def check_time_limit(self):
        """
        Check if the maximum runtime has been exceeded.
        Raises ResourceLimitExceeded if the limit is passed.
        """
        if self.start_time is None:
            raise RuntimeError("Checkpoint manager not started. Call start() first.")
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.max_runtime_seconds:
            # Save final state before raising
            if self.state:
                self.save_checkpoint()
            
            raise ResourceLimitExceeded(
                f"Maximum runtime of {format_duration(self.max_runtime_seconds)} exceeded. "
                f"Elapsed time: {format_duration(elapsed)}. "
                f"Process terminated gracefully. Checkpoint saved."
            )

    def should_checkpoint(self) -> bool:
        """Determine if enough time has passed to trigger a checkpoint."""
        if self.last_checkpoint_time is None:
            return False
        
        elapsed_since_last = time.time() - self.last_checkpoint_time
        return elapsed_since_last >= self.checkpoint_interval_seconds

    def update_iteration(self, iteration: int, metrics: Optional[Dict[str, Any]] = None):
        """Update the current iteration and optional metrics."""
        with self._lock:
            if self.state:
                self.state.iteration = iteration
                if metrics:
                    self.state.metrics.update(metrics)

    def save_checkpoint(self, force: bool = False) -> Optional[str]:
        """
        Save the current state to disk if enough time has passed or if forced.
        Returns the path to the saved checkpoint file, or None if not saved.
        """
        if self.start_time is None:
            logger.warning("Cannot save checkpoint: manager not started.")
            return None

        current_time = time.time()
        
        # Check if we should save
        if not force:
            if not self.should_checkpoint():
                return None

        with self._lock:
            if not self.state:
                return None
            
            self.state.last_checkpoint_time = current_time
            
            # Generate filename with timestamp
            timestamp = datetime.fromtimestamp(current_time).strftime("%Y%m%d_%H%M%S")
            filename = f"{self.checkpoint_prefix}_{timestamp}.json"
            filepath = self.checkpoint_dir / filename
            
            try:
                # Prepare serializable data
                data = {
                    "start_time": self.state.start_time,
                    "last_checkpoint_time": self.state.last_checkpoint_time,
                    "iteration": self.state.iteration,
                    "metrics": self.state.metrics,
                    "extra_data": self.state.extra_data
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Checkpoint saved to {filepath}")
                self.last_checkpoint_time = current_time
                return str(filepath)
                
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
                return None

    def load_latest_checkpoint(self) -> Optional[CheckpointState]:
        """Load the most recent checkpoint from disk."""
        if not self.checkpoint_dir.exists():
            return None
        
        checkpoints = sorted(self.checkpoint_dir.glob(f"{self.checkpoint_prefix}_*.json"))
        if not checkpoints:
            return None
        
        latest_file = checkpoints[-1]
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            self.state = CheckpointState(
                start_time=data["start_time"],
                last_checkpoint_time=data["last_checkpoint_time"],
                iteration=data["iteration"],
                metrics=data.get("metrics", {}),
                extra_data=data.get("extra_data", {})
            )
            self.start_time = data["start_time"]
            self.last_checkpoint_time = data["last_checkpoint_time"]
            self.current_iteration = data["iteration"]
            
            logger.info(f"Resumed from checkpoint: {latest_file}")
            return self.state
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {latest_file}: {e}")
            return None

    def get_elapsed_time(self) -> float:
        """Get the elapsed time since start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_remaining_time(self) -> float:
        """Get the remaining time before the limit."""
        elapsed = self.get_elapsed_time()
        return max(0.0, self.max_runtime_seconds - elapsed)

    def get_status(self) -> Dict[str, Any]:
        """Get a human-readable status summary."""
        elapsed = self.get_elapsed_time()
        remaining = self.get_remaining_time()
        progress_pct = (elapsed / self.max_runtime_seconds) * 100 if self.max_runtime_seconds > 0 else 0.0
        
        return {
            "elapsed": format_duration(elapsed),
            "remaining": format_duration(remaining),
            "progress_percent": f"{progress_pct:.2f}%",
            "iteration": self.current_iteration,
            "checkpoint_dir": str(self.checkpoint_dir),
            "max_runtime": format_duration(self.max_runtime_seconds)
        }

def run_with_checkpointing(
    func: Callable,
    checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR,
    max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
    checkpoint_interval_seconds: int = DEFAULT_CHECKPOINT_INTERVAL_SECONDS,
    *args,
    **kwargs
):
    """
    Decorator/helper to run a function with automatic checkpointing and time limits.
    
    This is a simple wrapper that creates a CheckpointManager and calls the function,
    checking time limits periodically if the function supports it (e.g., by checking
    a passed manager or by the function itself calling a callback).
    
    For complex pipelines, it's recommended to instantiate CheckpointManager directly
    and call check_time_limit() inside loops.
    """
    manager = CheckpointManager(
        checkpoint_dir=checkpoint_dir,
        max_runtime_seconds=max_runtime_seconds,
        checkpoint_interval_seconds=checkpoint_interval_seconds
    )
    manager.start()
    
    try:
        # If the function accepts a manager argument, pass it
        import inspect
        sig = inspect.signature(func)
        if 'checkpoint_manager' in sig.parameters:
            return func(*args, checkpoint_manager=manager, **kwargs)
        else:
            # Try to call without manager, but user must handle time checks internally
            logger.warning("Function does not accept checkpoint_manager. "
                         "Ensure it calls manager.check_time_limit() internally.")
            return func(*args, **kwargs)
    except ResourceLimitExceeded:
        logger.critical("Execution halted due to time limit.")
        raise
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        # Attempt to save state on error
        if manager.state:
            manager.save_checkpoint(force=True)
        raise

# Convenience function for scripts
def get_checkpoint_manager(
    checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR,
    max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
    checkpoint_interval_seconds: int = DEFAULT_CHECKPOINT_INTERVAL_SECONDS
) -> CheckpointManager:
    """Factory function to create a configured CheckpointManager."""
    return CheckpointManager(
        checkpoint_dir=checkpoint_dir,
        max_runtime_seconds=max_runtime_seconds,
        checkpoint_interval_seconds=checkpoint_interval_seconds
    )