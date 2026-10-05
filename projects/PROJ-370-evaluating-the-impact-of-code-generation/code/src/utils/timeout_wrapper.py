"""
Timeout wrapper module to enforce global runtime limits for the pipeline.

Implements FR-013: Enforce global 6h runtime limit.
- Logs warning to logs/timeout.log if limit exceeded.
- Exits with code 143 if limit exceeded.
- Supports checkpointing via state/timeout_checkpoint.json.
- Gracefully skips remaining PRs instead of hard exit.
"""

import os
import signal
import sys
import time
import logging
import json
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

from config.settings import get_paths, ensure_directories

# Constants
DEFAULT_TIMEOUT_SECONDS = 6 * 60 * 60  # 6 hours
CHECKPOINT_FILE = "state/timeout_checkpoint.json"
LOG_FILE = "logs/timeout.log"
EXIT_CODE_TIMEOUT = 143

logger = logging.getLogger(__name__)


class TimeoutExceeded(Exception):
    """Exception raised when the global timeout is exceeded."""
    pass


class TimeoutContext:
    """
    Context manager and state holder for timeout enforcement.
    Tracks start time, elapsed time, and checkpoint state.
    """

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds
        self.start_time: Optional[float] = None
        self.checkpoint_data: Dict[str, Any] = {}
        self._loaded = False

    def load_checkpoint(self) -> bool:
        """
        Load existing checkpoint from disk if it exists.
        Returns True if checkpoint was loaded, False otherwise.
        """
        paths = get_paths()
        checkpoint_path = paths["state_dir"] / CHECKPOINT_FILE

        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    self.checkpoint_data = json.load(f)
                self._loaded = True
                # Restore start time if present
                if "start_time_iso" in self.checkpoint_data:
                    start_dt = datetime.fromisoformat(self.checkpoint_data["start_time_iso"])
                    self.start_time = start_dt.timestamp()
                logger.info(f"Loaded timeout checkpoint from {checkpoint_path}")
                return True
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
                self.checkpoint_data = {}
                self._loaded = False
        return False

    def save_checkpoint(self, pr_id: Optional[str] = None, pr_count: int = 0) -> None:
        """
        Save current state to checkpoint file.
        """
        paths = get_paths()
        checkpoint_path = paths["state_dir"] / CHECKPOINT_FILE
        ensure_directories(paths["state_dir"])

        if self.start_time is None:
            self.start_time = time.time()

        self.checkpoint_data = {
            "start_time_iso": datetime.fromisoformat(datetime.fromtimestamp(self.start_time).isoformat()),
            "timeout_seconds": self.timeout_seconds,
            "last_update_iso": datetime.utcnow().isoformat(),
            "pr_id": pr_id,
            "pr_count": pr_count
        }

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(self.checkpoint_data, f, indent=2)

    def get_elapsed_seconds(self) -> float:
        """Calculate elapsed time since start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_remaining_seconds(self) -> float:
        """Calculate remaining time before timeout."""
        elapsed = self.get_elapsed_seconds()
        remaining = self.timeout_seconds - elapsed
        return max(0.0, remaining)

    def is_timeout_exceeded(self) -> bool:
        """Check if timeout has been exceeded."""
        return self.get_remaining_seconds() <= 0

    def check_and_raise(self, pr_id: Optional[str] = None) -> None:
        """
        Check if timeout is exceeded. If so, log warning and raise TimeoutExceeded.
        Saves checkpoint before raising.
        """
        if self.is_timeout_exceeded():
            self.save_checkpoint(pr_id=pr_id, pr_count=0)
            log_timeout_warning(pr_id)
            raise TimeoutExceeded(f"Global timeout of {self.timeout_seconds}s exceeded.")


# Global context instance
_global_context: Optional[TimeoutContext] = None


def setup_timeout_alarm(timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> TimeoutContext:
    """
    Initialize the global timeout context.
    Does NOT set a signal alarm (since we want graceful skipping, not hard kill).
    Instead, we check periodically in the main loop.
    """
    global _global_context
    _global_context = TimeoutContext(timeout_seconds=timeout_seconds)
    _global_context.load_checkpoint()
    
    if _global_context.start_time is None:
        _global_context.start_time = time.time()
        _global_context.save_checkpoint()
    
    logger.info(f"Timeout wrapper initialized. Limit: {timeout_seconds}s ({timeout_seconds/3600:.1f}h)")
    return _global_context


def cancel_timeout_alarm() -> None:
    """Cleanup function (no-op for this implementation since we don't use signal alarms)."""
    pass


def set_global_timeout(timeout_seconds: int) -> None:
    """Set global timeout if not already set."""
    global _global_context
    if _global_context is None:
        setup_timeout_alarm(timeout_seconds)
    else:
        _global_context.timeout_seconds = timeout_seconds


def get_timeout_context() -> Optional[TimeoutContext]:
    """Get the current timeout context."""
    return _global_context


def check_timeout(pr_id: Optional[str] = None) -> bool:
    """
    Check if timeout has been exceeded.
    Returns True if timeout exceeded, False otherwise.
    Raises TimeoutExceeded if exceeded.
    """
    if _global_context is None:
        return False
    
    _global_context.check_and_raise(pr_id)
    return False


def get_remaining_time_seconds() -> float:
    """Get remaining time before timeout."""
    if _global_context is None:
        return float('inf')
    return _global_context.get_remaining_seconds()


def log_timeout_warning(pr_id: Optional[str] = None) -> None:
    """
    Log a warning to the timeout log file.
    """
    paths = get_paths()
    log_path = paths["logs_dir"] / LOG_FILE
    ensure_directories(paths["logs_dir"])

    elapsed = _global_context.get_elapsed_seconds() if _global_context else 0
    remaining = _global_context.get_remaining_seconds() if _global_context else 0

    msg = (
        f"TIMEOUT EXCEEDED | "
        f"Elapsed: {elapsed:.1f}s | "
        f"Limit: {_global_context.timeout_seconds if _global_context else 0}s | "
        f"Remaining: {remaining:.1f}s | "
        f"PR: {pr_id or 'N/A'} | "
        f"Action: Skipping remaining PRs and exiting with code {EXIT_CODE_TIMEOUT}"
    )

    # Log to file
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} - {msg}\n")

    # Log to logger
    logger.warning(msg)


def enforce_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce timeout on a function.
    If timeout is exceeded, logs warning and raises TimeoutExceeded.
    """
    def wrapper(*args, **kwargs):
        check_timeout()
        return func(*args, **kwargs)
    return wrapper


def main() -> None:
    """
    Main entry point for testing the timeout wrapper standalone.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize paths
    paths = get_paths()
    ensure_directories(paths["state_dir"])
    ensure_directories(paths["logs_dir"])

    # Setup timeout (e.g., 10 seconds for testing)
    timeout_sec = 10
    ctx = setup_timeout_alarm(timeout_sec)

    print(f"Timeout set to {timeout_sec}s. Starting loop...")

    try:
        for i in range(20):
            check_timeout(pr_id=f"PR-{i}")
            print(f"Processing PR-{i}... {ctx.get_remaining_seconds():.1f}s remaining")
            time.sleep(1)
    except TimeoutExceeded as e:
        print(f"Timeout exceeded: {e}")
        print(f"Gracefully exiting with code {EXIT_CODE_TIMEOUT}")
        sys.exit(EXIT_CODE_TIMEOUT)

    print("Completed without timeout.")


if __name__ == "__main__":
    main()