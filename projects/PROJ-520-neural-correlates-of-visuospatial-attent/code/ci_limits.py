"""
CI Environment Configuration Management for CPU/RAM limits.

This module provides utilities to detect, enforce, and report
environment constraints (CPU cores, memory limits) typical of CI
runners. It ensures the pipeline respects these limits to prevent
OOM crashes or resource starvation.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import multiprocessing

# Attempt to import resource for Unix-like systems (Linux/macOS)
# Windows does not support resource.getrlimit in the same way
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

from config import load_config, get_paths

LOGGER = logging.getLogger(__name__)

# Default fallbacks if detection fails
DEFAULT_CPU_LIMIT = 2
DEFAULT_RAM_LIMIT_GB = 4.0

def get_cpu_count() -> int:
    """
    Detect the available CPU count.
    Prioritizes environment variables often set by CI (e.g., SLURM, GitHub Actions).
    Falls back to os.cpu_count().
    """
    # Check common CI environment variables
    ci_cpu = os.getenv('CI_CPU_LIMIT') or os.getenv('SLURM_CPUS_PER_TASK') or os.getenv('NUMBER_OF_PROCESSORS')
    if ci_cpu:
        try:
            count = int(ci_cpu)
            LOGGER.info(f"Detected CPU limit from env: {count}")
            return count
        except ValueError:
            LOGGER.warning(f"Invalid CPU limit in env: {ci_cpu}")

    # Fallback to standard library
    count = multiprocessing.cpu_count()
    if count:
        LOGGER.debug(f"Detected CPU count via multiprocessing: {count}")
        return count

    LOGGER.warning("Could not detect CPU count, defaulting to 2")
    return DEFAULT_CPU_LIMIT

def get_memory_limit_gb() -> float:
    """
    Detect the available memory limit in GB.
    Checks CI-specific environment variables and cgroup limits on Linux.
    """
    # Check common CI environment variables
    ci_ram = os.getenv('CI_RAM_LIMIT_GB') or os.getenv('SLURM_MEM_PER_NODE') or os.getenv('MEMORY_LIMIT_GB')
    if ci_ram:
        try:
            # SLURM sometimes reports in MB, others in GB. Assuming GB for explicit vars,
            # but checking for 'MB' suffix if present in string logic if needed.
            # For simplicity, assume the variable is in GB unless it looks like a huge MB number.
            val = float(ci_ram)
            if val > 1000: # Heuristic: likely MB if > 1000
                val = val / 1024.0
            LOGGER.info(f"Detected RAM limit from env: {val:.2f} GB")
            return val
        except ValueError:
            LOGGER.warning(f"Invalid RAM limit in env: {ci_ram}")

    if HAS_RESOURCE:
        try:
            # Get soft limit for memory (maxrss is virtual memory on some systems)
            # resource limits are in KB on Linux/macOS
            soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)
            if soft_limit != resource.RLIM_INFINITY and soft_limit > 0:
                limit_gb = soft_limit / (1024.0 ** 3)
                LOGGER.debug(f"Detected RLIMIT_AS: {limit_gb:.2f} GB")
                return limit_gb
        except Exception as e:
            LOGGER.debug(f"Could not read RLIMIT_AS: {e}")

    # Fallback
    LOGGER.warning(f"Could not detect RAM limit, defaulting to {DEFAULT_RAM_LIMIT_GB} GB")
    return DEFAULT_RAM_LIMIT_GB

def enforce_limits(cpu_limit: Optional[int] = None, ram_limit_gb: Optional[float] = None) -> Dict[str, Any]:
    """
    Enforce environment constraints by adjusting process settings.
    
    On Linux, this can set RLIMIT_AS if not already set by the runner.
    Returns a dictionary of the effective limits used.
    """
    effective_cpu = cpu_limit or get_cpu_count()
    effective_ram = ram_limit_gb or get_memory_limit_gb()

    # Ensure we don't claim more than physically available
    phys_cpu = multiprocessing.cpu_count()
    if effective_cpu > phys_cpu:
        LOGGER.warning(f"Requested CPU limit ({effective_cpu}) > physical ({phys_cpu}). Capping to {phys_cpu}.")
        effective_cpu = phys_cpu

    if HAS_RESOURCE:
        # Convert GB to bytes for RLIMIT_AS
        ram_bytes = int(effective_ram * (1024 ** 3))
        try:
            # Set soft and hard limit
            # Note: In CI, the runner might have already set a hard limit. 
            # We can only lower it or set the soft limit.
            current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
            if current_soft == resource.RLIM_INFINITY:
                # No limit set, apply our soft limit
                resource.setrlimit(resource.RLIMIT_AS, (ram_bytes, current_hard))
                LOGGER.info(f"Set RLIMIT_AS soft limit to {effective_ram:.2f} GB")
            elif current_soft < ram_bytes:
                LOGGER.info(f"RLIMIT_AS already set lower ({current_soft/(1024**3):.2f} GB). Using existing.")
            else:
                LOGGER.info(f"RLIMIT_AS already set higher. Using existing ({current_soft/(1024**3):.2f} GB).")
        except ValueError as e:
            LOGGER.warning(f"Could not set RLIMIT_AS: {e}")
        except Exception as e:
            LOGGER.warning(f"Error setting resource limits: {e}")

    return {
        "cpu_limit": effective_cpu,
        "ram_limit_gb": effective_ram,
        "cpu_count_physical": phys_cpu,
        "has_resource_module": HAS_RESOURCE
    }

def get_environment_report() -> Dict[str, Any]:
    """
    Generate a comprehensive report of the current environment constraints.
    """
    cpu = get_cpu_count()
    ram = get_memory_limit_gb()
    enforced = enforce_limits(cpu, ram)
    
    report = {
        "cpu_limit": enforced["cpu_limit"],
        "ram_limit_gb": round(enforced["ram_limit_gb"], 2),
        "cpu_count_physical": enforced["cpu_count_physical"],
        "has_resource_module": enforced["has_resource_module"],
        "timestamp": None # Usually handled by logger, but good for JSON export
    }
    
    LOGGER.info(f"Environment Report: CPU={report['cpu_limit']}, RAM={report['ram_limit_gb']}GB")
    return report

def main():
    """
    CLI entry point to print environment limits.
    Useful for CI logs to verify configuration.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Print CI environment limits")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    report = get_environment_report()

    if args.json:
        import json
        print(json.dumps(report, indent=2))
    else:
        print(f"CPU Limit: {report['cpu_limit']}")
        print(f"RAM Limit: {report['ram_limit_gb']} GB")
        print(f"Physical CPUs: {report['cpu_count_physical']}")

if __name__ == "__main__":
    main()
