import logging
import os
import gc
import sys
import warnings
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Try to import psutil for accurate memory monitoring, but fall back to
# a basic implementation if not available (common in minimal environments)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    warnings.warn("psutil not installed. Memory monitoring will use basic fallback.")

# Configuration
MEMORY_WARNING_THRESHOLD_MB = 4096  # 4 GB warning threshold
MEMORY_CRITICAL_THRESHOLD_MB = 7000  # 7 GB critical threshold (approx 80% of 8GB)
logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in Megabytes.

    Returns:
        float: Memory usage in MB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        # rss = Resident Set Size (physical memory)
        return process.memory_info().rss / (1024 * 1024)
    else:
        # Fallback for Linux using /proc/self/statm (page size * pages)
        if sys.platform.startswith('linux'):
            try:
                with open('/proc/self/statm', 'r') as f:
                    rss_pages = int(f.read().split()[1])
                page_size = os.sysconf('SC_PAGE_SIZE') / (1024 * 1024)
                return rss_pages * page_size
            except (IOError, ValueError):
                logger.warning("Could not read /proc/self/statm for memory stats.")
                return 0.0
        elif sys.platform == 'darwin':
            # macOS fallback: basic estimate or 0
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # ru_maxrss is in bytes on macOS
                return usage.ru_maxrss / (1024 * 1024)
            except Exception:
                return 0.0
        else:
            # Windows or unknown: return 0 or attempt basic estimate
            return 0.0


def get_system_memory_total_mb() -> float:
    """
    Get the total system memory in Megabytes.

    Returns:
        float: Total system memory in MB.
    """
    if HAS_PSUTIL:
        return psutil.virtual_memory().total / (1024 * 1024)
    else:
        # Fallback: try to read from /proc/meminfo on Linux
        if sys.platform.startswith('linux'):
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            # Value is in kB
                            return float(line.split()[1]) / 1024
            except IOError:
                pass
        # Default fallback
        return 16000.0  # Assume 16GB if unknown


def log_memory_snapshot(prefix: str = "Snapshot") -> None:
    """
    Logs the current memory usage to the configured logger.

    Args:
        prefix (str): A label for the snapshot.
    """
    current_mb = get_memory_usage_mb()
    total_mb = get_system_memory_total_mb()
    usage_pct = (current_mb / total_mb * 100) if total_mb > 0 else 0.0

    log_msg = f"{prefix}: Current Memory = {current_mb:.2f} MB ({usage_pct:.1f}% of {total_mb:.2f} MB)"
    logger.info(log_msg)

    if current_mb > MEMORY_CRITICAL_THRESHOLD_MB:
        logger.error(f"CRITICAL: Memory usage exceeds {MEMORY_CRITICAL_THRESHOLD_MB} MB. Consider reducing batch size or streaming.")
    elif current_mb > MEMORY_WARNING_THRESHOLD_MB:
        logger.warning(f"WARNING: Memory usage exceeds {MEMORY_WARNING_THRESHOLD_MB} MB.")


def force_gc_and_log() -> None:
    """
    Forces garbage collection and logs the resulting memory state.
    """
    logger.info("Forcing garbage collection...")
    gc.collect()
    log_memory_snapshot("After GC")


@contextmanager
def memory_monitor_context(threshold_mb: Optional[float] = None, check_interval: int = 1):
    """
    Context manager to monitor memory usage during a block of code.
    Logs warnings if usage exceeds thresholds.

    Args:
        threshold_mb (float, optional): Custom warning threshold in MB. Defaults to MEMORY_WARNING_THRESHOLD_MB.
        check_interval (int): How often to check memory (not implemented in this simple version, logs on entry/exit).
    """
    if threshold_mb is None:
        threshold_mb = MEMORY_WARNING_THRESHOLD_MB

    start_mb = get_memory_usage_mb()
    log_memory_snapshot(f"Start of Block (Threshold: {threshold_mb} MB)")

    try:
        yield
    finally:
        end_mb = get_memory_usage_mb()
        delta = end_mb - start_mb
        log_memory_snapshot(f"End of Block (Delta: {delta:.2f} MB)")

        if end_mb > threshold_mb:
            warnings.warn(f"Memory usage {end_mb:.2f} MB exceeded threshold {threshold_mb} MB during block execution.")


def check_memory_budget(required_mb: float, safety_factor: float = 1.2) -> bool:
    """
    Checks if the system has enough available memory for a required operation.

    Args:
        required_mb (float): Required memory in MB.
        safety_factor (float): Multiplier to ensure we don't hit limits (e.g., 1.2 means 20% headroom).

    Returns:
        bool: True if budget is sufficient, False otherwise.
    """
    current_mb = get_memory_usage_mb()
    total_mb = get_system_memory_total_mb()
    available_mb = total_mb - current_mb
    required_with_safety = required_mb * safety_factor

    if available_mb < required_with_safety:
        logger.error(f"Memory budget check failed: Need {required_with_safety:.2f} MB (with safety), but only {available_mb:.2f} MB available.")
        return False
    else:
        logger.debug(f"Memory budget check passed: Need {required_with_safety:.2f} MB, {available_mb:.2f} MB available.")
        return True


def main():
    """
    CLI entry point to test memory monitoring functions.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logger.info("=== Memory Monitor Test ===")
    log_memory_snapshot("Initial")

    logger.info("Testing context manager...")
    with memory_monitor_context(threshold_mb=1000):
        # Simulate some memory usage
        data = [i for i in range(1000000)]
        log_memory_snapshot("Inside Context")

    logger.info("Forcing GC...")
    force_gc_and_log()

    logger.info("Budget Check (Requesting 100MB):")
    if check_memory_budget(100):
        logger.info("Budget sufficient.")
    else:
        logger.warning("Budget insufficient.")


if __name__ == "__main__":
    main()