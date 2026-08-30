import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import multiprocessing

def get_cpu_count() -> int:
    """Get available CPU count."""
    return multiprocessing.cpu_count()

def get_memory_limit_gb() -> float:
    """Get memory limit in GB (default 7GB for CI)."""
    return 7.0

def enforce_limits(max_cpu: Optional[int] = None, max_memory_gb: Optional[float] = None) -> Tuple[int, float]:
    """
    Enforce CPU and memory limits.
    Returns the enforced limits.
    """
    cpu_limit = max_cpu if max_cpu is not None else 2
    memory_limit = max_memory_gb if max_memory_gb is not None else 7.0

    available_cpu = get_cpu_count()
    if available_cpu > cpu_limit:
        logging.warning(f"Available CPUs ({available_cpu}) exceed limit ({cpu_limit}). Using {cpu_limit}.")

    return cpu_limit, memory_limit

def get_environment_report() -> Dict[str, Any]:
    """Get current environment resource report."""
    return {
        'cpu_count': get_cpu_count(),
        'memory_limit_gb': get_memory_limit_gb()
    }

def main():
    """Main entry point for CI limits check."""
    report = get_environment_report()
    print(f"Environment Report: {report}")

if __name__ == "__main__":
    main()
