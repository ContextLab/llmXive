"""
CI Limits and Environment Reporting.
Provides functions to detect hardware constraints and enforce them.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import multiprocessing

# Importing from config is moved to function scope to avoid circular imports
# We only need config for path resolution if necessary, but here we rely on env vars or defaults.

logger = logging.getLogger(__name__)

def get_cpu_count() -> int:
    """Return the number of available CPUs."""
    try:
        return multiprocessing.cpu_count()
    except Exception as e:
        logger.warning(f"Could not determine CPU count: {e}. Defaulting to 1.")
        return 1

def get_memory_limit_gb() -> float:
    """
    Return memory limit in GB.
    Prioritizes CI environment variables, then physical memory.
    """
    # Check for common CI memory limit env vars (in GB)
    if "CI_MEMORY_LIMIT_GB" in os.environ:
        try:
            return float(os.environ["CI_MEMORY_LIMIT_GB"])
        except ValueError:
            pass

    # Check for GitHub Actions specific limit (usually 7GB for free tier)
    if os.environ.get("RUNNER_OS") == "Linux" and os.environ.get("GITHUB_ACTIONS"):
        # Standard free tier is often 7GB, but we can try to read cgroups if available
        # For safety, default to a conservative 7.0 if we detect GH Actions
        return 7.0

    # Fallback: Try to read /proc/meminfo on Linux
    if sys.platform == "linux":
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Value is in kB
                        mem_kb = int(line.split()[1])
                        return mem_kb / (1024 * 1024)  # Convert to GB
        except Exception:
            pass

    # Ultimate fallback
    return 8.0

def enforce_limits(max_cpu: Optional[int] = None, max_memory_gb: Optional[float] = None) -> Dict[str, Any]:
    """
    Enforce resource limits by logging warnings or adjusting internal state.
    Returns a report of enforced limits.
    """
    available_cpu = get_cpu_count()
    available_memory = get_memory_limit_gb()

    enforced_cpu = max_cpu if max_cpu is not None else available_cpu
    enforced_memory = max_memory_gb if max_memory_gb is not None else available_memory

    if available_cpu < enforced_cpu:
        logger.warning(f"Requested {enforced_cpu} CPUs, but only {available_cpu} available. Limiting to {available_cpu}.")
        enforced_cpu = available_cpu

    if available_memory < enforced_memory:
        logger.warning(f"Requested {enforced_memory}GB RAM, but only {available_memory}GB available. Limiting to {available_memory}.")
        enforced_memory = available_memory

    return {
        "cpu_limit": enforced_cpu,
        "memory_limit_gb": enforced_memory,
        "detected_cpu": available_cpu,
        "detected_memory_gb": available_memory
    }

def get_environment_report() -> Dict[str, Any]:
    """
    Generate a comprehensive report of the execution environment.
    This function avoids circular imports by not importing config at module load time.
    """
    cpu_count = get_cpu_count()
    mem_limit = get_memory_limit_gb()
    enforced = enforce_limits()

    report = {
        "platform": sys.platform,
        "python_version": sys.version,
        "cpu_count": cpu_count,
        "memory_limit_gb": mem_limit,
        "enforced_limits": enforced,
        "environment_variables": {
            k: v for k, v in os.environ.items()
            if k.startswith(("CI_", "GITHUB_", "RUNNER_"))
        }
    }

    logger.info(f"Environment Report: {report}")
    return report

def main():
    """CLI entry point for environment reporting."""
    report = get_environment_report()
    print(f"Environment Report:\n{report}")

if __name__ == "__main__":
    main()
