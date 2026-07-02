"""
Environment configuration management for memory limits and runtime caps.

This module provides utilities to check system memory availability and
set runtime resource limits for long-running processes like fMRIPrep.
"""
import os
import sys
import resource
from typing import Optional, Tuple

# Default constants (in bytes)
DEFAULT_MEMORY_LIMIT_GB = 16
DEFAULT_RUNTIME_LIMIT_HOURS = 24
MEMORY_WARNING_THRESHOLD = 0.9  # 90% of limit triggers warning

def _get_available_memory_gb() -> float:
    """
    Detect available system memory in GB.
    
    Returns:
        Available memory in GB. Returns a safe default if detection fails.
    """
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            mem_total = None
            mem_avail = None
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail = int(line.split()[1])
            
            if mem_total is not None and mem_avail is not None:
                # Convert kB to GB
                return mem_avail / (1024 ** 2)
            elif mem_total is not None:
                # Fallback: assume 70% available if MemAvailable not found
                return (mem_total * 0.7) / (1024 ** 2)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                mem_bytes = int(result.stdout.strip())
                return mem_bytes / (1024 ** 3)
        except Exception:
            pass
    
    # Safe default for unknown systems
    return 8.0

def _get_current_memory_usage_gb() -> float:
    """
    Get current process memory usage in GB.
    
    Returns:
        Current memory usage in GB.
    """
    if sys.platform.startswith("linux"):
        try:
            pid = os.getpid()
            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        return rss_kb / (1024 ** 2)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["ps", "-o", "rss=", "-p", str(os.getpid())],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                rss_kb = int(result.stdout.strip())
                return rss_kb / (1024 ** 2)
        except Exception:
            pass
    
    return 0.0

def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, str]:
    """
    Check if the system has sufficient available memory.
    
    Args:
        limit_gb: Required memory limit in GB. If None, uses DEFAULT_MEMORY_LIMIT_GB.
    
    Returns:
        Tuple of (is_sufficient: bool, message: str)
    
    Raises:
        None: Returns status tuple instead of raising.
    """
    if limit_gb is None:
        limit_gb = DEFAULT_MEMORY_LIMIT_GB
    
    available_gb = _get_available_memory_gb()
    current_usage_gb = _get_current_memory_usage_gb()
    
    # Check if available memory is sufficient
    if available_gb < limit_gb:
        return (
            False,
            f"Insufficient memory: Available {available_gb:.2f}GB < Required {limit_gb:.2f}GB"
        )
    
    # Check if current usage is too high
    usage_ratio = current_usage_gb / limit_gb
    if usage_ratio > MEMORY_WARNING_THRESHOLD:
        return (
            True,
            f"Warning: Current memory usage {current_usage_gb:.2f}GB is {usage_ratio:.1%} of limit"
        )
    
    return (True, f"Memory check passed: Available {available_gb:.2f}GB >= Required {limit_gb:.2f}GB")

def set_runtime_cap(hours: Optional[float] = None) -> Tuple[bool, str]:
    """
    Set a runtime cap for the current process.
    
    This function attempts to set the CPU time limit for the process.
    On Unix-like systems, it uses resource.setrlimit. On Windows, it
    logs a warning as hard limits are not available.
    
    Args:
        hours: Maximum runtime in hours. If None, uses DEFAULT_RUNTIME_LIMIT_HOURS.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if hours is None:
        hours = DEFAULT_RUNTIME_LIMIT_HOURS
    
    if sys.platform.startswith("win"):
        return (
            False,
            "Runtime limits not supported on Windows. Consider using external process managers."
        )
    
    try:
        # Convert hours to seconds
        seconds = int(hours * 3600)
        
        # Set both soft and hard limits
        resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
        
        return (
            True,
            f"Runtime cap set to {hours} hours ({seconds} seconds)"
        )
    except (ValueError, resource.error) as e:
        return (
            False,
            f"Failed to set runtime cap: {str(e)}"
        )

def get_env_config() -> dict:
    """
    Get current environment configuration summary.
    
    Returns:
        Dictionary with memory and runtime configuration details.
    """
    available_mem = _get_available_memory_gb()
    current_mem = _get_current_memory_usage_gb()
    
    return {
        "available_memory_gb": round(available_mem, 2),
        "current_memory_usage_gb": round(current_mem, 2),
        "default_memory_limit_gb": DEFAULT_MEMORY_LIMIT_GB,
        "default_runtime_limit_hours": DEFAULT_RUNTIME_LIMIT_HOURS,
        "platform": sys.platform,
        "memory_warning_threshold": MEMORY_WARNING_THRESHOLD
    }

def main():
    """CLI entry point for environment configuration checks."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Check and configure environment resource limits"
    )
    parser.add_argument(
        "--memory-limit",
        type=float,
        default=DEFAULT_MEMORY_LIMIT_GB,
        help=f"Memory limit in GB (default: {DEFAULT_MEMORY_LIMIT_GB})"
    )
    parser.add_argument(
        "--runtime-limit",
        type=float,
        default=DEFAULT_RUNTIME_LIMIT_HOURS,
        help=f"Runtime limit in hours (default: {DEFAULT_RUNTIME_LIMIT_HOURS})"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check limits without setting them"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Check memory
    mem_ok, mem_msg = check_memory_limit(args.memory_limit)
    
    if args.check_only:
        result = {
            "memory_check": {"status": "ok" if mem_ok else "fail", "message": mem_msg}
        }
    else:
        # Set runtime cap
        runtime_ok, runtime_msg = set_runtime_cap(args.runtime_limit)
        result = {
            "memory_check": {"status": "ok" if mem_ok else "fail", "message": mem_msg},
            "runtime_cap": {"status": "ok" if runtime_ok else "fail", "message": runtime_msg}
        }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Memory Check: {mem_msg}")
        if not args.check_only:
            print(f"Runtime Cap: {runtime_msg}")
        
        if not mem_ok:
            sys.exit(1)

if __name__ == "__main__":
    main()