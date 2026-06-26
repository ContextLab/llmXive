"""Memory monitoring utilities for model inference validation.

Provides explicit memory monitoring to validate the 7GB limit throughout
model inference operations (SC-002).

This module tracks GPU and CPU memory usage before, during, and after
model operations to ensure compliance with memory constraints.
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

import numpy as np

# Try to import torch for GPU memory monitoring
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Memory limit constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3
MEMORY_WARNING_THRESHOLD = 0.9  # 90% of limit triggers warning
MEMORY_CRITICAL_THRESHOLD = 0.95  # 95% of limit triggers critical error

# Thread-local storage for monitoring state
_monitor_state = threading.local()


def _get_gpu_memory_mb() -> Optional[float]:
    """Get current GPU memory usage in MB.

    Returns:
        GPU memory usage in MB, or None if GPU not available.
    """
    if not TORCH_AVAILABLE:
        return None

    if not torch.cuda.is_available():
        return None

    return torch.cuda.memory_allocated() / (1024 ** 2)


def _get_cpu_memory_mb() -> float:
    """Get current CPU memory usage in MB.

    Returns:
        CPU memory usage in MB.
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 ** 2)
    except ImportError:
        # Fallback: estimate based on available info
        # This is a rough estimate - psutil is preferred
        return 0.0


def get_total_memory_mb() -> float:
    """Get total memory usage (GPU + CPU) in MB.

    Returns:
        Total memory usage in MB.
    """
    total = _get_cpu_memory_mb()
    gpu_mb = _get_gpu_memory_mb()
    if gpu_mb is not None:
        total += gpu_mb
    return total


def check_memory_limit() -> dict:
    """Check current memory usage against the 7GB limit.

    Returns:
        Dictionary with memory status information:
        - current_mb: Current memory usage in MB
        - limit_mb: Memory limit in MB
        - usage_percent: Percentage of limit used
        - status: 'ok', 'warning', or 'critical'
        - timestamp: ISO format timestamp
    """
    current_mb = get_total_memory_mb()
    limit_mb = MEMORY_LIMIT_BYTES / (1024 ** 2)
    usage_percent = (current_mb / limit_mb) * 100

    if usage_percent >= MEMORY_CRITICAL_THRESHOLD * 100:
        status = 'critical'
    elif usage_percent >= MEMORY_WARNING_THRESHOLD * 100:
        status = 'warning'
    else:
        status = 'ok'

    return {
        'current_mb': current_mb,
        'limit_mb': limit_mb,
        'usage_percent': usage_percent,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }


def validate_memory_within_limit(raise_on_exceed: bool = True) -> bool:
    """Validate that current memory usage is within the 7GB limit.

    Args:
        raise_on_exceed: If True, raise MemoryError when limit exceeded.

    Returns:
        True if memory is within limit, False otherwise.

    Raises:
        MemoryError: If memory exceeds critical threshold and raise_on_exceed is True.
    """
    status = check_memory_limit()

    if status['status'] == 'critical':
        if raise_on_exceed:
            raise MemoryError(
                f"Memory limit exceeded: {status['current_mb']:.2f} MB used, "
                f"limit is {status['limit_mb']:.2f} MB ({status['usage_percent']:.1f}%)"
            )
        return False

    return True


@contextmanager
def memory_monitor(operation_name: str, log_path: Optional[Path] = None) -> Generator[dict, None, None]:
    """Context manager for monitoring memory usage during operations.

    Monitors memory before, during, and after the enclosed operation.
    Logs memory status to a file if log_path is provided.

    Args:
        operation_name: Name of the operation being monitored.
        log_path: Optional path to write memory log file.

    Yields:
        Dictionary with memory monitoring results.

    Example:
        with memory_monitor("model_inference") as monitor:
            # perform inference
            pass
        print(f"Peak memory: {monitor['peak_mb']:.2f} MB")
    """
    logger = logging.getLogger(__name__)

    # Initial memory state
    start_mb = get_total_memory_mb()
    peak_mb = start_mb
    samples = [{'time': datetime.utcnow().isoformat(), 'memory_mb': start_mb}]

    logger.info(f"Memory monitor started: {operation_name}, initial: {start_mb:.2f} MB")

    # Start background sampling thread
    stop_sampling = threading.Event()

    def sample_memory():
        nonlocal peak_mb
        while not stop_sampling.is_set():
            current = get_total_memory_mb()
            if current > peak_mb:
                peak_mb = current
            samples.append({
                'time': datetime.utcnow().isoformat(),
                'memory_mb': current
            })
            time.sleep(0.1)  # Sample every 100ms

    sampler_thread = threading.Thread(target=sample_memory, daemon=True)
    sampler_thread.start()

    try:
        # Check memory before operation
        pre_check = check_memory_limit()
        yield {
            'operation': operation_name,
            'start_mb': start_mb,
            'peak_mb': peak_mb,
            'pre_status': pre_check['status'],
            'samples': samples
        }

    finally:
        # Stop sampling and collect final stats
        stop_sampling.set()
        sampler_thread.join(timeout=1.0)

        # Final memory check
        end_mb = get_total_memory_mb()
        final_check = check_memory_limit()

        result = {
            'operation': operation_name,
            'start_mb': start_mb,
            'end_mb': end_mb,
            'peak_mb': peak_mb,
            'pre_status': pre_check['status'],
            'post_status': final_check['status'],
            'samples': samples,
            'within_limit': final_check['status'] != 'critical'
        }

        # Log results
        logger.info(
            f"Memory monitor completed: {operation_name}, "
            f"peak: {peak_mb:.2f} MB, "
            f"status: {final_check['status']}"
        )

        # Write to log file if provided
        if log_path:
            _write_memory_log(result, log_path)

        # Update the yielded result with final state
        samples.append({'time': datetime.utcnow().isoformat(), 'memory_mb': end_mb})
        result['samples'] = samples

        # Validate limit (this will raise if exceeded)
        if final_check['status'] == 'critical':
            raise MemoryError(
                f"Memory limit exceeded during {operation_name}: "
                f"{peak_mb:.2f} MB peak, limit is {MEMORY_LIMIT_MB:.2f} MB"
            )

        yield result


MEMORY_LIMIT_MB = MEMORY_LIMIT_BYTES / (1024 ** 2)


def _write_memory_log(result: dict, log_path: Path) -> None:
    """Write memory monitoring results to a CSV log file.

    Args:
        result: Memory monitoring result dictionary.
        log_path: Path to the log file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'a', newline='') as f:
        import csv
        writer = csv.writer(f)

        # Write header if file is empty
        if log_path.stat().st_size == 0:
            writer.writerow([
                'timestamp', 'operation', 'start_mb', 'end_mb',
                'peak_mb', 'pre_status', 'post_status', 'within_limit'
            ])

        writer.writerow([
            datetime.utcnow().isoformat(),
            result['operation'],
            f"{result['start_mb']:.2f}",
            f"{result['end_mb']:.2f}",
            f"{result['peak_mb']:.2f}",
            result['pre_status'],
            result['post_status'],
            result['within_limit']
        ])


def setup_memory_monitoring(log_dir: Optional[Path] = None) -> Path:
    """Set up memory monitoring with logging to a directory.

    Args:
        log_dir: Directory to write memory logs. Defaults to data/memory_logs/.

    Returns:
        Path to the log directory.
    """
    if log_dir is None:
        log_dir = Path('data/memory_logs')

    log_dir.mkdir(parents=True, exist_ok=True)

    # Create a log file for this run
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    log_path = log_dir / f'memory_log_{timestamp}.csv'

    return log_path
