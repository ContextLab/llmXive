"""
Environment configuration management for memory limits and runtime caps.

This module provides utilities to check available system memory, enforce
memory limits using resource constraints, and set runtime execution caps.
"""
import os
import sys
import resource
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Default configuration constants
DEFAULT_MEMORY_LIMIT_GB = 14.0  # GB
DEFAULT_RUNTIME_CAP_SECONDS = 3600  # 1 hour
MEMORY_WARNING_THRESHOLD = 0.9  # 90% of limit triggers warning
MEMORY_HARD_THRESHOLD = 1.0  # 100% of limit triggers error


def get_available_memory_gb() -> float:
    """
    Get the total available system memory in GB.

    Returns:
        float: Available memory in gigabytes.

    Raises:
        OSError: If memory information cannot be retrieved.
    """
    try:
        # Linux: Read from /proc/meminfo
        if sys.platform.startswith('linux'):
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        # Value is in kB
                        parts = line.split()
                        mem_kb = int(parts[1])
                        return mem_kb / (1024 * 1024)
        # macOS: Use sysctl
        elif sys.platform == 'darwin':
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True,
                text=True,
                check=True
            )
            mem_bytes = int(result.stdout.strip())
            return mem_bytes / (1024 * 1024 * 1024)
        # Windows: Use psutil if available, otherwise fallback
        elif sys.platform == 'win32':
            try:
                import psutil
                return psutil.virtual_memory().total / (1024 * 1024 * 1024)
            except ImportError:
                logger.warning("psutil not installed on Windows. Using fallback.")
                return 8.0  # Conservative fallback
        else:
            logger.warning(f"Unknown platform {sys.platform}. Using fallback memory estimate.")
            return 8.0  # Conservative fallback

    except Exception as e:
        logger.error(f"Failed to retrieve memory information: {e}")
        return 8.0  # Conservative fallback


def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Check if the system has sufficient memory available for the configured limit.

    This function compares the available system memory against a specified limit
    (or a default if none is provided). It returns a tuple indicating whether
    the limit is satisfied and the actual available memory.

    Args:
        limit_gb (float, optional): Memory limit in GB. If None, uses DEFAULT_MEMORY_LIMIT_GB.

    Returns:
        Tuple[bool, float]: (is_satisfied, available_memory_gb)
            - is_satisfied: True if available memory >= limit_gb
            - available_memory_gb: The actual available memory in GB

    Raises:
        RuntimeError: If memory check fails due to system error.
    """
    try:
        available = get_available_memory_gb()
        limit = limit_gb if limit_gb is not None else DEFAULT_MEMORY_LIMIT_GB

        is_satisfied = available >= limit

        if not is_satisfied:
            logger.warning(
                f"Memory check failed: Available {available:.2f} GB < Required {limit:.2f} GB"
            )
        else:
            logger.info(
                f"Memory check passed: Available {available:.2f} GB >= Required {limit:.2f} GB"
            )

        return is_satisfied, available

    except Exception as e:
        logger.error(f"Error during memory limit check: {e}")
        raise RuntimeError(f"Memory limit check failed: {e}") from e


def set_runtime_cap(
    memory_limit_gb: Optional[float] = None,
    time_limit_seconds: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Set runtime resource caps for the current process.

    This function configures:
    1. Virtual memory limit (ulimit -v) to prevent excessive RAM usage.
    2. CPU time limit (ulimit -t) to prevent runaway processes.

    These limits are enforced by the operating system and will cause the
    process to terminate if exceeded.

    Args:
        memory_limit_gb (float, optional): Soft memory limit in GB.
            If None, uses DEFAULT_MEMORY_LIMIT_GB.
        time_limit_seconds (int, optional): CPU time limit in seconds.
            If None, uses DEFAULT_RUNTIME_CAP_SECONDS.

    Returns:
        Tuple[bool, str]: (success, message)
            - success: True if limits were set successfully
            - message: Status message describing the result

    Note:
        - On Windows, resource.setrlimit for memory may not be fully supported.
        - Time limits require POSIX compliance (Unix/Linux/macOS).
    """
    try:
        limit_gb = memory_limit_gb if memory_limit_gb is not None else DEFAULT_MEMORY_LIMIT_GB
        time_sec = time_limit_seconds if time_limit_seconds is not None else DEFAULT_RUNTIME_CAP_SECONDS

        # Convert GB to bytes for resource limits
        memory_bytes = int(limit_gb * 1024 * 1024 * 1024)

        # Set virtual memory limit (RLIMIT_AS)
        # Note: RLIMIT_AS is the virtual address space limit
        try:
            current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            logger.info(f"Set virtual memory limit to {limit_gb:.2f} GB")
        except (ValueError, resource.error) as e:
            # Some systems may not support RLIMIT_AS or may have constraints
            logger.warning(f"Could not set RLIMIT_AS: {e}. Proceeding without memory cap.")

        # Set CPU time limit (RLIMIT_CPU)
        if sys.platform != 'win32':
            try:
                resource.setrlimit(resource.RLIMIT_CPU, (time_sec, time_sec))
                logger.info(f"Set CPU time limit to {time_sec} seconds")
            except (ValueError, resource.error) as e:
                logger.warning(f"Could not set RLIMIT_CPU: {e}. Proceeding without time cap.")
        else:
            logger.warning("Windows does not support RLIMIT_CPU. Time cap not enforced.")

        return True, f"Resource caps set: Memory={limit_gb:.2f}GB, Time={time_sec}s"

    except Exception as e:
        error_msg = f"Failed to set runtime caps: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_env_config() -> dict:
    """
    Retrieve the current environment configuration.

    Returns:
        dict: Configuration dictionary containing:
            - memory_limit_gb: Current memory limit setting
            - time_limit_seconds: Current time limit setting
            - available_memory_gb: System available memory
            - platform: Operating system platform
    """
    available_mem = get_available_memory_gb()
    return {
        "memory_limit_gb": DEFAULT_MEMORY_LIMIT_GB,
        "time_limit_seconds": DEFAULT_RUNTIME_CAP_SECONDS,
        "available_memory_gb": available_mem,
        "platform": sys.platform,
        "limits_set": resource.getrlimit(resource.RLIMIT_AS) != (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
    }


def main():
    """
    CLI entry point for environment configuration management.

    Performs a diagnostic check of system resources and prints configuration status.
    """
    print("=== Environment Configuration Check ===")
    
    config = get_env_config()
    print(f"Platform: {config['platform']}")
    print(f"Available Memory: {config['available_memory_gb']:.2f} GB")
    print(f"Configured Memory Limit: {config['memory_limit_gb']:.2f} GB")
    print(f"Configured Time Limit: {config['time_limit_seconds']} seconds")
    print(f"Limits Currently Active: {config['limits_set']}")
    
    print("\n--- Checking Memory Limit ---")
    is_ok, avail = check_memory_limit()
    if is_ok:
        print(f"✓ Memory requirement satisfied ({avail:.2f} GB available)")
    else:
        print(f"✗ Memory requirement NOT satisfied ({avail:.2f} GB available)")
    
    print("\n--- Setting Runtime Caps ---")
    success, msg = set_runtime_cap()
    print(f"Result: {msg}")
    
    print("\n=== Configuration Complete ===")


if __name__ == "__main__":
    main()