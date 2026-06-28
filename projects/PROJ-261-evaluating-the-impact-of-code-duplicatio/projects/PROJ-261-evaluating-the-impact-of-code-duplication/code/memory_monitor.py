"""
Memory monitoring module for enforcing memory limits during inference.

Implements SC-002 by tracking memory usage throughout model inference
and providing alerts when limits are approached.
"""
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from config import get_memory_limit_mb

# Configure logging
logger = logging.getLogger(__name__)

# Memory monitoring state
_monitoring_active = False
_monitor_thread: Optional[threading.Thread] = None
_peak_memory_mb = 0.0
_memory_samples: list = []
_limit_mb = get_memory_limit_mb()

def get_total_memory_mb() -> float:
    """
    Get current total memory usage in megabytes.

    Returns:
        Current memory usage in MB.
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        logger.warning("psutil not available, using fallback memory estimate")
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get memory info: {e}")
        return 0.0

def check_memory_limit(current_mb: float = None) -> bool:
    """
    Check if current memory usage is within the configured limit.

    Args:
        current_mb: Optional current memory usage (computed if not provided).

    Returns:
        True if within limit, False if exceeded.
    """
    if current_mb is None:
        current_mb = get_total_memory_mb()

    if current_mb > _limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f}MB > {_limit_mb}MB")
        return False
    return True

def validate_memory_within_limit() -> bool:
    """
    Validate that memory is within limits and log status.

    Returns:
        True if within limit, False otherwise.
    """
    current = get_total_memory_mb()
    if check_memory_limit(current):
        logger.info(f"Memory within limit: {current:.2f}MB / {_limit_mb}MB")
        return True
    return False

def _memory_monitor_loop(
    interval: float = 1.0,
    callback: Optional[callable] = None
) -> None:
    """
    Background thread for continuous memory monitoring.

    Args:
        interval: Sampling interval in seconds.
        callback: Optional callback function for each sample.
    """
    global _peak_memory_mb, _monitoring_active

    while _monitoring_active:
        try:
            current = get_total_memory_mb()
            _memory_samples.append((datetime.now().isoformat(), current))

            if current > _peak_memory_mb:
                _peak_memory_mb = current
                logger.info(f"New peak memory: {_peak_memory_mb:.2f}MB")

            if callback:
                callback(current)

        except Exception as e:
            logger.error(f"Memory monitoring error: {e}")

        time.sleep(interval)

def setup_memory_monitoring(
    interval: float = 1.0,
    callback: Optional[callable] = None
) -> None:
    """
    Start background memory monitoring.

    Args:
        interval: Sampling interval in seconds.
        callback: Optional callback function for each sample.
    """
    global _monitoring_active, _monitor_thread

    if _monitoring_active:
        logger.warning("Memory monitoring already active")
        return

    _monitoring_active = True
    _monitor_thread = threading.Thread(
        target=_memory_monitor_loop,
        args=(interval, callback),
        daemon=True
    )
    _monitor_thread.start()
    logger.info(f"Memory monitoring started (interval: {interval}s)")

def stop_memory_monitoring() -> None:
    """Stop background memory monitoring."""
    global _monitoring_active, _monitor_thread

    _monitoring_active = False
    if _monitor_thread:
        _monitor_thread.join(timeout=2.0)
        _monitor_thread = None
    logger.info("Memory monitoring stopped")

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage observed during monitoring.

    Returns:
        Peak memory in MB.
    """
    return _peak_memory_mb

def get_memory_samples() -> list:
    """
    Get all memory samples collected during monitoring.

    Returns:
        List of (timestamp, memory_mb) tuples.
    """
    return _memory_samples.copy()

def save_memory_log(output_path: Path = None) -> None:
    """
    Save memory monitoring log to a file.

    Args:
        output_path: Optional output path (default: data/analysis/memory_log.csv).
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent / 'data' / 'analysis' / 'memory_log.csv'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('timestamp,memory_mb,peak_mb\n')
        for timestamp, memory in _memory_samples:
            f.write(f'{timestamp},{memory:.2f},{_peak_memory_mb:.2f}\n')

    logger.info(f"Memory log saved to {output_path}")

@contextmanager
def memory_monitor(
    limit_mb: int = None,
    interval: float = 1.0
) -> Generator[dict, None, None]:
    """
    Context manager for memory monitoring during a block of code.

    Args:
        limit_mb: Optional memory limit override.
        interval: Monitoring interval in seconds.

    Yields:
        Dictionary with monitoring statistics.

    Raises:
        MemoryError: If memory limit is exceeded.
    """
    global _limit_mb, _peak_memory_mb, _memory_samples

    old_limit = _limit_mb
    old_peak = _peak_memory_mb
    old_samples = _memory_samples

    if limit_mb:
        _limit_mb = limit_mb
    _peak_memory_mb = 0.0
    _memory_samples = []

    _monitoring_active = True
    try:
        monitor_thread = threading.Thread(
            target=_memory_monitor_loop,
            args=(interval, None),
            daemon=True
        )
        monitor_thread.start()

        result = {
            'start_memory': get_total_memory_mb(),
            'peak_memory': 0.0,
            'samples': []
        }

        yield result

        monitor_thread.join(timeout=1.0)
        result['end_memory'] = get_total_memory_mb()
        result['peak_memory'] = _peak_memory_mb
        result['samples'] = _memory_samples.copy()

    finally:
        _monitoring_active = False
        _limit_mb = old_limit
        _peak_memory_mb = old_peak
        _memory_samples = old_samples

    if result['peak_memory'] > _limit_mb:
        raise MemoryError(
            f"Memory limit exceeded: {result['peak_memory']:.2f}MB > {_limit_mb}MB"
        )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("Memory monitor module loaded")
    logger.info(f"Default memory limit: {_limit_mb}MB")