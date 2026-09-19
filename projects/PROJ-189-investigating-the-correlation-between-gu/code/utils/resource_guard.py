"""
Resource Guard Module for llmXive Pipeline.

Provides execution guards to ensure:
1. CPU-only execution (no GPU acceleration).
2. Memory usage stays within 7GB limit.
3. Execution time stays within 6 hours.

These guards are critical for the automated science pipeline to prevent
resource exhaustion on shared infrastructure.
"""

import os
import sys
import time
import logging
import threading
from datetime import timedelta
from typing import Optional, Callable, Any

from .logging import get_logger, get_memory_usage_mb

# Constants
MAX_MEMORY_GB = 7.0
MAX_MEMORY_MB = MAX_MEMORY_GB * 1024
MAX_TIME_HOURS = 6.0
MAX_TIME_SECONDS = MAX_TIME_HOURS * 3600
CHECK_INTERVAL_SECONDS = 5.0

logger = get_logger(__name__)


class ResourceLimitExceededError(Exception):
    """Raised when a resource limit (memory or time) is exceeded."""
    pass


class GPUForbiddenError(Exception):
    """Raised if GPU acceleration is detected when CPU-only is required."""
    pass


def check_cpu_only() -> None:
    """
    Verify that no GPU acceleration libraries are active or configured.
    
    Raises:
        GPUForbiddenError: If GPU usage is detected (e.g., CUDA available).
    """
    # Check for PyTorch GPU
    try:
        import torch
        if torch.cuda.is_available():
            raise GPUForbiddenError(
                "GPU acceleration detected via PyTorch. "
                "Set CUDA_VISIBLE_DEVICES='' or remove torch usage to run CPU-only."
            )
    except ImportError:
        pass  # PyTorch not installed, which is fine

    # Check for TensorFlow GPU
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            raise GPUForbiddenError(
                "GPU acceleration detected via TensorFlow. "
                "Ensure TF is configured for CPU-only execution."
            )
    except ImportError:
        pass  # TensorFlow not installed, which is fine

    # Check for environment variables forcing GPU
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_visible and cuda_visible != '-1':
        # Allow empty string or '-1' for CPU-only, but warn if set to specific IDs
        logger.warning(
            "CUDA_VISIBLE_DEVICES is set to '%s'. "
            "This may enable GPU acceleration. "
            "Ensure this is intentional for CPU-only execution.",
            cuda_visible
        )

    logger.info("CPU-only check passed: No GPU acceleration detected.")


class ResourceMonitor:
    """
    Context manager and decorator to enforce resource limits during execution.
    
    Monitors memory usage and execution time, raising exceptions if limits are exceeded.
    """

    def __init__(
        self,
        max_memory_mb: float = MAX_MEMORY_MB,
        max_time_seconds: float = MAX_TIME_SECONDS,
        check_interval: float = CHECK_INTERVAL_SECONDS
    ):
        self.max_memory_mb = max_memory_mb
        self.max_time_seconds = max_time_seconds
        self.check_interval = check_interval
        self.start_time: Optional[float] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        self.last_memory_mb: float = 0.0
        self._lock = threading.Lock()

    def _monitor_loop(self) -> None:
        """Background loop to check memory and time periodically."""
        while not self.stop_monitoring.is_set():
            current_time = time.time()
            elapsed = current_time - self.start_time if self.start_time else 0

            # Check time limit
            if elapsed > self.max_time_seconds:
                self._raise_limit_exceeded("Time", self.max_time_seconds, elapsed, "seconds")

            # Check memory limit
            current_memory = get_memory_usage_mb()
            with self._lock:
                self.last_memory_mb = current_memory

            if current_memory > self.max_memory_mb:
                self._raise_limit_exceeded(
                    "Memory",
                    self.max_memory_mb,
                    current_memory,
                    "MB"
                )

            self.stop_monitoring.wait(self.check_interval)

    def _raise_limit_exceeded(
        self,
        resource_name: str,
        limit: float,
        current: float,
        unit: str
    ) -> None:
        """Helper to raise a ResourceLimitExceededError with formatted details."""
        raise ResourceLimitExceededError(
            f"{resource_name} limit exceeded: "
            f"Current usage is {current:.2f} {unit}, "
            f"limit is {limit:.2f} {unit}."
        )

    def __enter__(self) -> 'ResourceMonitor':
        self.start_time = time.time()
        self.stop_monitoring.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(
            "Resource monitor started: "
            f"Max Memory={self.max_memory_mb:.0f}MB, Max Time={self.max_time_seconds/3600:.1f}h"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop_monitoring.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        if exc_type is None:
            elapsed = time.time() - self.start_time if self.start_time else 0
            logger.info(
                f"Resource monitor finished: "
                f"Elapsed time={elapsed:.2f}s, Peak memory={self.last_memory_mb:.2f}MB"
            )
        else:
            logger.error(f"Resource monitor interrupted by exception: {exc_val}")

    def __call__(self, func: Callable) -> Callable:
        """Decorator usage."""
        def wrapper(*args, **kwargs) -> Any:
            with self:
                return func(*args, **kwargs)
        return wrapper


def enforce_resource_limits(func: Callable) -> Callable:
    """
    Decorator to enforce CPU-only execution and resource limits on a function.
    
    This decorator:
    1. Checks for CPU-only execution before running the function.
    2. Wraps the function execution in a ResourceMonitor context.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs) -> Any:
        # 1. Check CPU-only
        check_cpu_only()
        
        # 2. Run with resource monitoring
        with ResourceMonitor():
            return func(*args, **kwargs)
    return wrapper


def main() -> None:
    """
    CLI entry point for testing resource guards.
    
    Usage:
        python -m code.utils.resource_guard
    """
    logger.info("Starting resource guard CLI test...")
    
    # Test 1: CPU-only check
    try:
        check_cpu_only()
        logger.info("✓ CPU-only check passed.")
    except GPUForbiddenError as e:
        logger.error(f"✗ CPU-only check failed: {e}")
        sys.exit(1)

    # Test 2: ResourceMonitor with a dummy long-running function
    def dummy_work():
        logger.info("Starting dummy work...")
        time.sleep(2)
        logger.info("Dummy work completed.")
        return "Success"

    monitor = ResourceMonitor(max_time_seconds=10, check_interval=0.5)
    
    try:
        with monitor:
            result = dummy_work()
        logger.info(f"✓ Resource monitor test passed. Result: {result}")
    except ResourceLimitExceededError as e:
        logger.error(f"✗ Resource limit exceeded: {e}")
        sys.exit(1)

    # Test 3: Decorator usage
    @enforce_resource_limits
    def decorated_work():
        time.sleep(1)
        return "Decorated success"

    try:
        result = decorated_work()
        logger.info(f"✓ Decorator test passed. Result: {result}")
    except (GPUForbiddenError, ResourceLimitExceededError) as e:
        logger.error(f"✗ Decorator test failed: {e}")
        sys.exit(1)

    logger.info("All resource guard tests passed.")


if __name__ == "__main__":
    main()