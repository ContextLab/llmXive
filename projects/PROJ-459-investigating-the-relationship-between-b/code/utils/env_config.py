"""
Environment configuration management for memory limits and runtime caps.

This module provides utilities to check available system memory, enforce
memory limits, and set runtime resource caps to prevent OOM crashes during
heavy fMRI processing tasks.
"""
import os
import sys
import resource
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Default constants
DEFAULT_MEMORY_LIMIT_GB = 12.0
DEFAULT_RUNTIME_CAP_SECONDS = 3600  # 1 hour
MEMORY_WARNING_THRESHOLD = 0.85  # Warn if usage > 85% of limit
MEMORY_FAIL_THRESHOLD = 0.95     # Fail if usage > 95% of limit

def get_available_memory_gb() -> float:
    """
    Detect available physical memory in GB.

    Returns:
        float: Available memory in GB.
    """
    try:
        if sys.platform == "darwin" or sys.platform == "linux":
            # Use resource.getrusage for RSS or os.sysconf for total
            # For a robust check of *available* memory, we check /proc/meminfo on Linux
            if sys.platform == "linux" and os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    lines = f.readlines()
                mem_info = {}
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(":")
                        val = int(parts[1])  # in kB
                        mem_info[key] = val
                
                # Available memory (Linux 3.14+ has MemAvailable)
                if "MemAvailable" in mem_info:
                    avail_kb = mem_info["MemAvailable"]
                elif "MemFree" in mem_info and "Buffers" in mem_info and "Cached" in mem_info:
                    avail_kb = mem_info["MemFree"] + mem_info["Buffers"] + mem_info["Cached"]
                else:
                    # Fallback: Total - Used (RSS of current process approx)
                    avail_kb = mem_info.get("MemTotal", 0) - mem_info.get("MemFree", 0)
                
                return avail_kb / (1024 * 1024)
            else:
                # macOS or fallback: use resource.getrusage (approximate max RSS of current)
                # This is less accurate for *system* available, but safe for process limits
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # maxrss is in KB on macOS, bytes on some Linux configs? 
                # Actually on macOS it's KB. On Linux getrusage returns KB in ru_maxrss.
                # To get system total, we might need psutil, but sticking to stdlib:
                # We will estimate system total if possible, otherwise return a safe default
                # Let's try to get total system memory via os.sysconf if available
                if hasattr(os, 'sysconf') and hasattr(os.sysconf, 'SC_PHYS_PAGES'):
                    page_size = os.sysconf('SC_PAGE_SIZE')
                    total_pages = os.sysconf('SC_PHYS_PAGES')
                    return (total_pages * page_size) / (1024 * 1024 * 1024)
                else:
                    logger.warning("Could not determine system memory precisely. Defaulting to 16GB.")
                    return 16.0
        else:
            # Windows fallback
            logger.warning("Memory detection not implemented for Windows. Defaulting to 16GB.")
            return 16.0
    except Exception as e:
        logger.error(f"Error detecting memory: {e}")
        return 16.0

def check_memory_limit(limit_gb: Optional[float] = None, fail_fast: bool = True) -> Tuple[bool, float, float]:
    """
    Check if the system has enough available memory for the requested limit.

    Args:
        limit_gb: Required memory in GB. If None, uses DEFAULT_MEMORY_LIMIT_GB.
        fail_fast: If True, raises RuntimeError if limit is insufficient.

    Returns:
        Tuple[bool, float, float]: (is_ok, available_gb, limit_gb)

    Raises:
        RuntimeError: If fail_fast is True and memory is insufficient.
    """
    limit = limit_gb if limit_gb is not None else DEFAULT_MEMORY_LIMIT_GB
    available = get_available_memory_gb()
    
    is_ok = available >= limit
    
    logger.info(f"Memory Check: Available {available:.2f} GB, Required {limit:.2f} GB. Status: {'OK' if is_ok else 'FAIL'}")
    
    if not is_ok and fail_fast:
        raise RuntimeError(
            f"Insufficient memory. Available: {available:.2f} GB, Required: {limit:.2f} GB. "
            "Cannot proceed with fMRI processing."
        )
    
    return is_ok, available, limit

def set_runtime_cap(seconds: Optional[int] = None, memory_mb: Optional[int] = None) -> None:
    """
    Set hard limits on runtime and memory for the current process.

    This uses `resource.setrlimit` to enforce constraints. If the process
    exceeds these limits, the OS will terminate it (SIGXCPU or SIGSEGV).

    Args:
        seconds: Maximum CPU time in seconds. If None, uses DEFAULT_RUNTIME_CAP_SECONDS.
        memory_mb: Maximum virtual memory in MB. If None, no memory limit is set via this function
                   (rely on check_memory_limit or container limits).
    """
    if sys.platform == "win32":
        logger.warning("set_runtime_cap not supported on Windows (resource module unavailable).")
        return

    cap_time = seconds if seconds is not None else DEFAULT_RUNTIME_CAP_SECONDS
    
    # Set CPU time limit (soft and hard)
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cap_time, cap_time))
        logger.info(f"Set CPU time limit: {cap_time} seconds.")
    except (ValueError, resource.error) as e:
        logger.warning(f"Could not set CPU time limit: {e}")

    if memory_mb is not None:
        try:
            # RLIMIT_AS: maximum address space size
            resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024, memory_mb * 1024 * 1024))
            logger.info(f"Set memory limit: {memory_mb} MB.")
        except (ValueError, resource.error) as e:
            logger.warning(f"Could not set memory limit: {e}")

def get_env_config() -> Dict[str, any]:
    """
    Retrieve current environment configuration status.

    Returns:
        Dict containing memory status and configured limits.
    """
    return {
        "available_memory_gb": get_available_memory_gb(),
        "default_memory_limit_gb": DEFAULT_MEMORY_LIMIT_GB,
        "default_runtime_cap_seconds": DEFAULT_RUNTIME_CAP_SECONDS,
        "platform": sys.platform
    }

def main():
    """
    CLI entry point for environment configuration checks.
    """
    logging.basicConfig(level=logging.INFO)
    
    print("=== Environment Configuration Check ===")
    config = get_env_config()
    print(f"Platform: {config['platform']}")
    print(f"Available Memory: {config['available_memory_gb']:.2f} GB")
    print(f"Default Memory Limit: {config['default_memory_limit_gb']} GB")
    print(f"Default Runtime Cap: {config['default_runtime_cap_seconds']} seconds")
    
    print("\nRunning check_memory_limit()...")
    try:
        is_ok, avail, lim = check_memory_limit(fail_fast=True)
        print(f"Result: OK (Available: {avail:.2f} GB >= Limit: {lim:.2f} GB)")
    except RuntimeError as e:
        print(f"Result: FAILED - {e}")
        sys.exit(1)
    
    print("\nSetting runtime caps...")
    set_runtime_cap(seconds=300, memory_mb=8000)
    print("Caps set successfully.")

if __name__ == "__main__":
    main()