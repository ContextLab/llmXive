"""
Resource monitoring wrapper for enforcing CPU time and RAM limits.

This module provides:
* A context manager ``_resource_monitor`` that checks resource usage.
* A decorator ``limit_resources`` that enforces limits and writes a JSON
  usage report to ``data/resource_usage.json``.
* A decorator ``resource_monitor`` (the name expected by existing
  pipeline scripts) that accepts the legacy keyword arguments
  ``runtime_limit_h`` and ``memory_limit_gb`` and forwards them to
  ``limit_resources``.
"""

import os
import sys
import time
import resource
import logging
import threading
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Callable, Any
from functools import wraps

# Configure logger for this module
logger = logging.getLogger(__name__)

class ResourceLimitExceeded(Exception):
    """Exception raised when a resource limit is exceeded."""
    pass


def get_current_ram_mb() -> float:
    """
    Get the current RAM usage of the process in MB.

    Returns:
        float: Current RAM usage in MB
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, MB on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss / 1024.0


def get_current_cpu_time() -> float:
    """
    Get the cumulative CPU time used by the process in seconds.

    Returns:
        float: CPU time in seconds
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def _get_env_limit(var_name: str, default_seconds: float, unit_factor: float = 1.0) -> float:
    """
    Helper to read a limit from environment variables, overriding defaults.

    Args:
        var_name: Environment variable name (e.g., 'RUNTIME_LIMIT_H')
        default_seconds: Default limit in seconds
        unit_factor: Multiplier for the input unit (e.g., 3600 for hours to seconds)

    Returns:
        float: The limit in seconds
    """
    env_val = os.environ.get(var_name)
    if env_val is not None:
        try:
            val = float(env_val)
            # Convert from hours to seconds if the variable implies hours
            if 'H' in var_name or 'HOURS' in var_name:
                return val * 3600.0
            # If it's GB for memory, convert to MB
            if 'GB' in var_name and 'RAM' in var_name:
                return val * 1024.0
            return val * unit_factor
        except ValueError:
            logger.warning(f"Invalid value for {var_name}: {env_val}. Using default.")
    return default_seconds


@contextmanager
def _resource_monitor(
    cpu_limit: Optional[float] = None,
    ram_limit: Optional[float] = None,
    check_interval: float = 60.0  # Check every 60 seconds
):
    """
    Context manager to monitor CPU time and RAM usage.

    Args:
        cpu_limit: Maximum allowed CPU time in seconds. If None, reads from
                   RUNTIME_LIMIT_H env var, else defaults to 6h.
        ram_limit: Maximum allowed RAM in MB. If None, reads from
                   MEMORY_LIMIT_GB env var, else defaults to 7GB.
        check_interval: Interval between resource checks in seconds (default: 60s)

    Yields:
        None

    Raises:
        ResourceLimitExceeded: If CPU time or RAM limit is exceeded
    """
    # Determine limits: Env Var -> Argument -> Default
    if cpu_limit is None:
        cpu_limit = _get_env_limit('RUNTIME_LIMIT_H', 6 * 3600)

    if ram_limit is None:
        ram_limit = _get_env_limit('MEMORY_LIMIT_GB', 7 * 1024)

    start_time = time.time()
    last_check_time = start_time

    # Start monitoring thread
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=_monitor_resources,
        args=(cpu_limit, ram_limit, check_interval, stop_event),
        daemon=True
    )
    monitor_thread.start()

    try:
        yield
    except Exception as e:
        raise e
    finally:
        stop_event.set()
        monitor_thread.join(timeout=1.0)

        # Final check
        current_cpu = get_current_cpu_time()
        current_ram = get_current_ram_mb()

        if current_cpu > cpu_limit:
            raise ResourceLimitExceeded(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )
        if current_ram > ram_limit:
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )


def _monitor_resources(
    cpu_limit: float,
    ram_limit: float,
    check_interval: float,
    stop_event: threading.Event
):
    """
    Background thread function to monitor resources.

    Args:
        cpu_limit: Maximum allowed CPU time in seconds
        ram_limit: Maximum allowed RAM in MB
        check_interval: Interval between checks in seconds
        stop_event: Event to signal thread to stop
    """
    while not stop_event.is_set():
        if stop_event.wait(timeout=check_interval):
            break

        current_cpu = get_current_cpu_time()
        current_ram = get_current_ram_mb()

        logger.info(
            f"Resource check - CPU: {current_cpu:.2f}s / {cpu_limit:.2f}s, "
            f"RAM: {current_ram:.2f}MB / {ram_limit:.2f}MB"
        )

        if current_cpu > cpu_limit:
            logger.error(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )
            raise ResourceLimitExceeded(
                f"CPU time limit exceeded: {current_cpu:.2f}s > {cpu_limit:.2f}s"
            )

        if current_ram > ram_limit:
            logger.error(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram:.2f}MB > {ram_limit:.2f}MB"
            )


def enforce_resource_limits(
    cpu_limit: Optional[float] = None,
    ram_limit: Optional[float] = None,
    check_interval: float = 60.0  # Check every 60 seconds
):
    """
    Decorator to enforce resource limits on a function.

    Args:
        cpu_limit: Maximum allowed CPU time in seconds. If None, reads from
                   RUNTIME_LIMIT_H env var, else defaults to 6h.
        ram_limit: Maximum allowed RAM in MB. If None, reads from
                   MEMORY_LIMIT_GB env var, else defaults to 7GB.
        check_interval: Interval between resource checks in seconds (default: 60s)

    Returns:
        Callable: Wrapped function with resource monitoring
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with _resource_monitor(
                cpu_limit=cpu_limit,
                ram_limit=ram_limit,
                check_interval=check_interval
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ----------------------------------------------------------------------
# Helper functions for the @limit_resources decorator
# ----------------------------------------------------------------------
def _read_limits_from_config() -> tuple:
    """
    Reads runtime (seconds) and memory (MB) limits from ``config.yaml``.
    If the file is missing or malformed, falls back to the defaults
    (6 h runtime, 7 GB RAM).

    Returns:
        (cpu_limit_seconds, ram_limit_mb)
    """
    import yaml

    default_cpu = 6 * 3600          # 6 hours → seconds
    default_ram = 7 * 1024          # 7 GB → MB

    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    if not config_path.is_file():
        return default_cpu, default_ram

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        limits = cfg.get("resource_limits", {})
        cpu_h = limits.get("max_time_hours", 6)
        ram_gb = limits.get("max_memory_gb", 7)
        return float(cpu_h) * 3600.0, float(ram_gb) * 1024.0
    except Exception as exc:
        logger.warning(f"Failed to read config.yaml ({exc}); using defaults.")
        return default_cpu, default_ram


def _write_resource_report(runtime_seconds: float, peak_ram_mb: float):
    """
    Writes a JSON report ``data/resource_usage.json`` containing the
    runtime (seconds) and peak RAM usage (GB).

    The file is created under the project root, and any missing parent
    directories are created automatically.
    """
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / "data" / "resource_usage.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "runtime_seconds": round(runtime_seconds, 3),
        "peak_ram_gb": round(peak_ram_mb / 1024.0, 3)
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Resource usage report written to {output_path}")


def limit_resources(
    cpu_limit: Optional[float] = None,
    ram_limit: Optional[float] = None,
    check_interval: float = 60.0
):
    """
    Decorator that enforces resource limits (using the same logic as
    :func:`enforce_resource_limits`) **and** records the actual usage
    after the wrapped function finishes. The usage statistics are saved
    to ``data/resource_usage.json`` as required by task T001.

    Parameters
    ----------
    cpu_limit : float, optional
        Maximum CPU time in seconds. If ``None`` the value is read from
        ``config.yaml`` or the corresponding environment variable.
    ram_limit : float, optional
        Maximum RAM usage in MB. If ``None`` the value is read from
        ``config.yaml`` or the corresponding environment variable.
    check_interval : float, default 60.0
        How often the background monitor checks resource usage.

    Returns
    -------
    Callable
        The wrapped function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve limits if they were not supplied explicitly
            resolved_cpu, resolved_ram = _read_limits_from_config()
            cpu = cpu_limit if cpu_limit is not None else resolved_cpu
            ram = ram_limit if ram_limit is not None else resolved_ram

            start_cpu = get_current_cpu_time()
            start_ram = get_current_ram_mb()

            # Run the function inside the monitoring context
            with _resource_monitor(cpu_limit=cpu, ram_limit=ram, check_interval=check_interval):
                result = func(*args, **kwargs)

            # After successful execution, compute deltas
            end_cpu = get_current_cpu_time()
            end_ram = get_current_ram_mb()
            runtime = end_cpu - start_cpu
            peak_ram = max(start_ram, end_ram)

            # Write the JSON report
            _write_resource_report(runtime, peak_ram)

            return result
        return wrapper
    return decorator


# ----------------------------------------------------------------------
# Compatibility decorator expected by existing pipeline scripts
# ----------------------------------------------------------------------
def resource_monitor(*, runtime_limit_h: Optional[float] = None,
                    memory_limit_gb: Optional[float] = None,
                    check_interval: float = 60.0):
    """
    Legacy decorator used throughout the pipeline. It forwards the
    ``runtime_limit_h`` (hours) and ``memory_limit_gb`` arguments to the
    :func:`limit_resources` decorator.

    Example:
        @resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
        def my_func():
            ...

    Returns:
        Callable: the wrapped function.
    """
    cpu_seconds = runtime_limit_h * 3600.0 if runtime_limit_h is not None else None
    ram_mb = memory_limit_gb * 1024.0 if memory_limit_gb is not None else None
    return limit_resources(cpu_limit=cpu_seconds, ram_limit=ram_mb, check_interval=check_interval)


def main():
    """
    Demo function to test resource monitoring and the @limit_resources decorator.
    """
    @limit_resources()
    def test_function():
        print("Running test function...")
        time.sleep(2)
        return "Success"

    try:
        result = test_function()
        print(f"Result: {result}")
    except ResourceLimitExceeded as e:
        print(f"Resource limit exceeded: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
