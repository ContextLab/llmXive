"""
Resource monitoring utilities for the llmXive automated science pipeline.

This module enforces system resource limits (RAM, CPU) to ensure stable execution.
"""

from __future__ import annotations

import os
from typing import Optional

import psutil

from logging.pipeline_logger import get_logger
from utils.error_handler import PipelineError, log_and_exit


def enforce_limits(
    max_memory_gb: float = 6.0,
    max_cpu_cores: float = 2.0,
    check_interval_seconds: float = 1.0,
) -> None:
    """
    Monitor system resources and abort if limits are exceeded.

    This function checks memory usage and CPU count against specified limits.
    If limits are breached, it logs an error and exits.

    Args:
        max_memory_gb: Maximum allowed RAM in GB.
        max_cpu_cores: Maximum allowed CPU cores.
        check_interval_seconds: Interval between checks (not used in this blocking check).

    Raises:
        PipelineError: If limits are exceeded.
    """
    logger = get_logger()

    # Check CPU count
    cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)
    if cpu_count is None:
        log_and_exit("Could not determine CPU count", "E007")

    if cpu_count > max_cpu_cores:
        log_and_exit(
            f"CPU core limit exceeded: {cpu_count} > {max_cpu_cores}",
            "E008",
        )

    # Check memory usage
    mem_info = psutil.virtual_memory()
    memory_used_gb = mem_info.used / (1024**3)

    if memory_used_gb > max_memory_gb:
        log_and_exit(
            f"Memory limit exceeded: {memory_used_gb:.2f} GB > {max_memory_gb} GB",
            "E009",
        )

    logger.info(
        f"Resource check passed: CPU={cpu_count}, Memory Used={memory_used_gb:.2f} GB"
    )
