"""
Utility functions for performance monitoring and compliance reporting.
"""
import os
import sys
import shutil
import resource
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from config import get_data_dir

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    Handles differences between Linux (KB) and macOS (bytes).
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == 'darwin':
            # macOS: ru_maxrss is in bytes
            return usage.ru_maxrss / (1024 * 1024)
        else:
            # Linux/Unix: ru_maxrss is in KB
            return usage.ru_maxrss / 1024
    except Exception as e:
        logging.warning(f"Could not get memory usage: {e}")
        return 0.0

def get_disk_usage_gb(path: Optional[Path] = None) -> float:
    """
    Get disk usage in GB for the specified path.
    Defaults to the project's data directory.
    """
    if path is None:
        path = get_data_dir()

    try:
        total, used, free = shutil.disk_usage(path)
        return used / (1024 ** 3)
    except Exception as e:
        logging.warning(f"Could not get disk usage for {path}: {e}")
        return 0.0

def check_compliance(
    runtime_seconds: float,
    memory_mb: float,
    disk_gb: float,
    limits: Dict[str, int],
    thresholds: Dict[str, float]
) -> Dict[str, Any]:
    """
    Check if the given metrics are within GitHub Actions limits and thresholds.
    Returns a compliance report.
    """
    compliance = {}
    warnings = []

    # Runtime
    compliance["runtime"] = "PASS" if runtime_seconds <= limits["max_runtime_seconds"] else "FAIL"
    if runtime_seconds > thresholds["runtime_seconds"]:
        warnings.append(f"Runtime ({runtime_seconds:.1f}s) exceeds 80% of limit ({thresholds['runtime_seconds']:.1f}s)")

    # Memory
    compliance["memory"] = "PASS" if memory_mb <= limits["max_memory_mb"] else "FAIL"
    if memory_mb > thresholds["memory_mb"]:
        warnings.append(f"Peak memory ({memory_mb:.1f}MB) exceeds 80% of limit ({thresholds['memory_mb']:.1f}MB)")

    # Disk
    compliance["disk"] = "PASS" if disk_gb <= limits["max_disk_gb"] else "FAIL"
    if disk_gb > thresholds["disk_gb"]:
        warnings.append(f"Disk usage ({disk_gb:.2f}GB) exceeds 80% of limit ({thresholds['disk_gb']:.2f}GB)")

    overall = "COMPLIANT" if all(status == "PASS" for status in compliance.values()) else "NON-COMPLIANT"

    return {
        "compliance_status": compliance,
        "warnings": warnings,
        "overall_status": overall
    }
