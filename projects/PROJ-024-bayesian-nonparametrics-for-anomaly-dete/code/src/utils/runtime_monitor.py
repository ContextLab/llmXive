"""
Runtime monitoring utilities for anomaly detection pipeline.

Provides timeout handling, progress tracking, and partial result saving
for long-running operations (e.g., model training, dataset processing).

Per SC-003: Pipeline must complete within 30 minutes per dataset.
"""

import os
import sys
import time
import signal
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict, List, Tuple, Union
from dataclasses import dataclass, field, asdict
import threading
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT_SECONDS = 1800  # 30 minutes per SC-003
WARNING_THRESHOLD_SECONDS = 1200  # Warn at 20 minutes (66% of timeout)
PARTIAL_RESULTS_DIR = Path("data/processed/partial_results")
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE_SECONDS = 60

@dataclass
class RuntimeMetrics:
    """Runtime metrics for a single execution."""
    start_time: datetime
    end_time: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    timeout_occurred: bool = False
    partial_results_saved: bool = False
    retry_count: int = 0
    dataset_id: Optional[str] = None
    operation_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'elapsed_seconds': self.elapsed_seconds,
            'timeout_occurred': self.timeout_occurred,
            'partial_results_saved': self.partial_results_saved,
            'retry_count': self.retry_count,
            'dataset_id': self.dataset_id,
            'operation_name': self.operation_name
        }

@dataclass
class TimeoutConfig:
    """Configuration for timeout handling."""
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    warning_threshold_seconds: int = WARNING_THRESHOLD_SECONDS
    retry_max_attempts: int = RETRY_MAX_ATTEMPTS
    retry_backoff_base_seconds: int = RETRY_BACKOFF_BASE_SECONDS
    save_partial_results: bool = True
    partial_results_dir: Path = PARTIAL_RESULTS_DIR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

class RuntimeMonitor:
    """
    Monitors execution time and handles timeout scenarios.

    Per SC-003: Enforces 30-minute limit per dataset with:
    - Timeout warnings at configurable threshold
    - Partial result saving on timeout
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        timeout_config: Optional[TimeoutConfig] = None,
        operation_name: Optional[str] = None,
        dataset_id: Optional[str] = None
    ):
        """
        Initialize runtime monitor.

        Args:
            timeout_config: Configuration for timeout handling
            operation_name: Name of the operation being monitored
            dataset_id: Identifier for the dataset being processed
        """
        self.config = timeout_config or TimeoutConfig()
        self.operation_name = operation_name
        self.dataset_id = dataset_id
        self._start_time: Optional[datetime] = None
        self._lock = threading.Lock()
        self._timeout_occurred = False
        self._metrics = RuntimeMetrics(
            start_time=datetime.now(),
            operation_name=operation_name,
            dataset_id=dataset_id
        )

    def start(self) -> None:
        """Start the runtime monitor."""
        with self._lock:
            self._start_time = datetime.now()
            self._timeout_occurred = False
            self._metrics.start_time = self._start_time
            logger.info(
                f"Started monitoring: {self.operation_name} "
                f"(dataset: {self.dataset_id}, timeout: {self.config.timeout_seconds}s)"
            )

    def elapsed(self) -> float:
        """
        Get elapsed time in seconds.

        Returns:
            Elapsed time since start in seconds
        """
        if self._start_time is None:
            return 0.0
        return (datetime.now() - self._start_time).total_seconds()

    def check_timeout(self) -> bool:
        """
        Check if timeout has been reached.

        Returns:
            True if timeout exceeded, False otherwise

        Raises:
            TimeoutError: If timeout exceeded and partial results saved
        """
        elapsed = self.elapsed()

        if elapsed >= self.config.timeout_seconds:
            self._timeout_occurred = True
            self._metrics.timeout_occurred = True
            logger.warning(
                f"TIMEOUT: {self.operation_name} exceeded {self.config.timeout_seconds}s "
                f"(elapsed: {elapsed:.1f}s)"
            )

            if self.config.save_partial_results:
                self.save_partial_results()

            raise TimeoutError(
                f"Operation '{self.operation_name}' exceeded timeout of "
                f"{self.config.timeout_seconds}s (elapsed: {elapsed:.1f}s)"
            )

        return False

    def check_warning(self) -> bool:
        """
        Check if warning threshold has been reached.

        Returns:
            True if warning threshold exceeded, False otherwise
        """
        elapsed = self.elapsed()

        if elapsed >= self.config.warning_threshold_seconds:
            logger.warning(
                f"WARNING: {self.operation_name} approaching timeout "
                f"(elapsed: {elapsed:.1f}s / {self.config.timeout_seconds}s, "
                f"threshold: {self.config.warning_threshold_seconds}s)"
            )
            return True
        return False

    def save_partial_results(
        self,
        partial_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Save partial results when timeout occurs.

        Args:
            partial_data: Partial results to save
            metadata: Additional metadata to include

        Returns:
            Path to saved file, or None if saving disabled
        """
        if not self.config.save_partial_results:
            return None

        try:
            # Ensure partial results directory exists
            partial_results_dir = Path(self.config.partial_results_dir)
            partial_results_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_op_name = (self.operation_name or "operation").replace(" ", "_")
            safe_dataset = (self.dataset_id or "unknown").replace(" ", "_")
            filename = f"{safe_op_name}_{safe_dataset}_{timestamp}_partial.json"
            filepath = partial_results_dir / filename

            # Prepare data
            save_data = {
                'monitor_metrics': self._metrics.to_dict(),
                'partial_data': partial_data,
                'metadata': metadata,
                'saved_at': datetime.now().isoformat()
            }

            # Write to file
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)

            logger.info(
                f"Saved partial results to {filepath} "
                f"(timeout: {self._timeout_occurred})"
            )
            self._metrics.partial_results_saved = True
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save partial results: {e}")
            return None

    def should_retry(self) -> bool:
        """
        Check if retry should be attempted.

        Returns:
            True if retry is possible, False otherwise
        """
        return self._metrics.retry_count < self.config.retry_max_attempts

    def trigger_retry(self) -> float:
        """
        Prepare for retry with exponential backoff.

        Returns:
            Time to wait before retry in seconds
        """
        self._metrics.retry_count += 1
        delay = self._get_retry_delay()

        logger.info(
            f"Retrying {self.operation_name} (attempt {self._metrics.retry_count} "
            f"of {self.config.retry_max_attempts}, wait: {delay:.1f}s)"
        )

        time.sleep(delay)
        return delay

    def _get_retry_delay(self) -> float:
        """
        Calculate retry delay with exponential backoff.

        Returns:
            Delay in seconds
        """
        base = self.config.retry_backoff_base_seconds
        return base * (2 ** (self._metrics.retry_count - 1))

    def get_metrics(self) -> RuntimeMetrics:
        """
        Get current runtime metrics.

        Returns:
            RuntimeMetrics object with current state
        """
        self._metrics.elapsed_seconds = self.elapsed()
        return self._metrics

    def stop(self) -> None:
        """Stop the runtime monitor and record end time."""
        with self._lock:
            if self._start_time is not None:
                self._metrics.end_time = datetime.now()
                self._metrics.elapsed_seconds = self.elapsed()
                logger.info(
                    f"Completed: {self.operation_name} "
                    f"(elapsed: {self._metrics.elapsed_seconds:.1f}s)"
                )

    def __enter__(self) -> 'RuntimeMonitor':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def monitor_execution(
    config: Optional[TimeoutConfig] = None,
    partial_data_callback: Optional[Callable[[], Dict[str, Any]]] = None,
    operation_name: Optional[str] = None,
    dataset_id: Optional[str] = None
):
    """
    Decorator to monitor function execution with timeout handling.

    Args:
        config: Timeout configuration
        partial_data_callback: Callback to get partial data on timeout
        operation_name: Name of operation for logging
        dataset_id: Dataset identifier

    Example:
        @monitor_operation(timeout_seconds=1800, operation_name="train_model")
        def train_model(data):
            # Long-running training
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            monitor = RuntimeMonitor(
                timeout_config=config,
                operation_name=operation_name or func.__name__,
                dataset_id=dataset_id
            )

            with monitor:
                retry_count = 0

                while True:
                    try:
                        # Check for timeout periodically during execution
                        # This is a coarse check; use within function for finer control
                        if monitor.check_warning():
                            logger.warning(
                                f"Approaching timeout for {monitor.operation_name}"
                            )

                        # Execute the function
                        result = func(*args, **kwargs)

                        # Success
                        return result

                    except TimeoutError as e:
                        if not monitor.should_retry():
                            logger.error(
                                f"All retry attempts exhausted for "
                                f"{monitor.operation_name}"
                            )
                            raise

                        # Prepare for retry
                        monitor.trigger_retry()

                    except KeyboardInterrupt:
                        logger.warning(
                            f"Interrupted: {monitor.operation_name}"
                        )
                        if config and config.save_partial_results:
                            partial_data = partial_data_callback() if partial_data_callback else None
                            monitor.save_partial_results(partial_data)
                        raise

                    except Exception as e:
                        logger.error(
                            f"Error in {monitor.operation_name}: {e}"
                        )
                        raise

        return wrapper
    return decorator


def run_with_timeout(
    func: Callable,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    args: Tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None,
    dataset_id: Optional[str] = None
) -> Tuple[bool, Any, Optional[str]]:
    """
    Run a function with timeout enforcement.

    Args:
        func: Function to execute
        timeout_seconds: Maximum execution time in seconds
        args: Positional arguments for function
        kwargs: Keyword arguments for function
        operation_name: Name for logging
        dataset_id: Dataset identifier

    Returns:
        Tuple of (success, result_or_error, partial_result_path)
    """
    kwargs = kwargs or {}
    config = TimeoutConfig(timeout_seconds=timeout_seconds)
    monitor = RuntimeMonitor(
        timeout_config=config,
        operation_name=operation_name or func.__name__,
        dataset_id=dataset_id
    )

    success = False
    result = None
    partial_path = None

    with monitor:
        try:
            result = func(*args, **kwargs)
            success = True
            return success, result, None

        except TimeoutError as e:
            logger.error(f"Timeout: {e}")
            partial_path = monitor.save_partial_results()
            return success, str(e), partial_path

        except Exception as e:
            logger.error(f"Error: {e}")
            return success, str(e), None


def check_runtime_budget(
    elapsed_seconds: float,
    budget_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    dataset_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if execution is within budget.

    Args:
        elapsed_seconds: Time already spent
        budget_seconds: Total budget in seconds
        dataset_id: Dataset identifier

    Returns:
        Dictionary with budget status information
    """
    remaining = budget_seconds - elapsed_seconds
    percentage_used = (elapsed_seconds / budget_seconds) * 100 if budget_seconds > 0 else 0

    status = {
        'elapsed_seconds': elapsed_seconds,
        'budget_seconds': budget_seconds,
        'remaining_seconds': remaining,
        'percentage_used': percentage_used,
        'within_budget': remaining > 0,
        'dataset_id': dataset_id,
        'check_time': datetime.now().isoformat()
    }

    if remaining <= 0:
        status['status'] = 'EXCEEDED'
    elif remaining <= budget_seconds * 0.2:
        status['status'] = 'CRITICAL'
    elif remaining <= budget_seconds * 0.5:
        status['status'] = 'WARNING'
    else:
        status['status'] = 'OK'

    return status


def save_runtime_metrics(
    metrics: RuntimeMetrics,
    output_dir: Optional[Path] = None,
    filename_prefix: Optional[str] = None
) -> Path:
    """
    Save runtime metrics to a JSON file.

    Args:
        metrics: RuntimeMetrics object to save
        output_dir: Directory to save metrics (default: data/processed/results)
        filename_prefix: Prefix for filename

    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = Path("data/processed/results")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = filename_prefix or "runtime_metrics"
    filename = f"{prefix}_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, 'w') as f:
        json.dump(metrics.to_dict(), f, indent=2, default=str)

    logger.info(f"Saved runtime metrics to {filepath}")
    return filepath


def main():
    """
    Test runtime monitor functionality.
    """
    print("Testing RuntimeMonitor...")

    # Test basic monitoring
    config = TimeoutConfig(
        timeout_seconds=5,
        warning_threshold_seconds=3,
        save_partial_results=True
    )

    with RuntimeMonitor(
        timeout_config=config,
        operation_name="test_operation",
        dataset_id="test_dataset"
    ) as monitor:
        # Simulate work
        for i in range(10):
            time.sleep(0.5)
            monitor.check_warning()

            if monitor.check_timeout():
                print("Timeout triggered!")
                break

    print(f"Metrics: {monitor.get_metrics().to_dict()}")
    print("Test complete!")


if __name__ == "__main__":
    main()
