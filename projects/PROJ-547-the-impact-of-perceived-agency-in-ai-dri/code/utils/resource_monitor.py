"""
Resource monitoring utilities for the pipeline.

Provides functions to monitor and enforce resource limits such as memory usage
and CPU cores, ensuring the pipeline operates within specified constraints.
"""

from __future__ import annotations

import os
from typing import Optional

import psutil

from logging.pipeline_logger import get_logger
from utils.error_handler import PipelineError, log_and_exit

def enforce_limits(
    max_memory_gb: float = 6.0,
    max_cpu_cores: int = 2,
    check_interval: float = 1.0,
) -> None:
    """
    Enforce resource limits for the pipeline.

    This function monitors the current process's resource usage and raises
    a PipelineError if the limits are exceeded. It is intended to be called
    periodically during long-running operations.

    Args:
        max_memory_gb: Maximum allowed memory usage in gigabytes. Default is 6.0.
        max_cpu_cores: Maximum allowed number of CPU cores. Default is 2.
        check_interval: Interval in seconds between checks. Default is 1.0.

    Raises:
        PipelineError: If memory usage exceeds max_memory_gb or CPU usage
            exceeds max_cpu_cores.
    """
    logger = get_logger()
    process = psutil.Process(os.getpid())

    # Check memory usage
    memory_info = process.memory_info()
    memory_gb = memory_info.rss / (1024**3)

    if memory_gb > max_memory_gb:
        error_msg = (
            f"Memory usage ({memory_gb:.2f} GB) exceeds limit ({max_memory_gb} GB)"
        )
        logger.error(error_msg)
        raise PipelineError(error_msg)

    # Check CPU usage
    cpu_percent = process.cpu_percent(interval=check_interval)
    cpu_cores_used = cpu_percent / 100.0

    if cpu_cores_used > max_cpu_cores:
        error_msg = (
            f"CPU usage ({cpu_cores_used:.2f} cores) exceeds limit ({max_cpu_cores} cores)"
        )
        logger.warning(error_msg)
        # Note: We log a warning for CPU usage rather than raising an error,
        # as CPU usage can fluctuate and may not always indicate a problem.
        # However, if this becomes a critical issue, it can be changed to an error.

    logger.debug(
        f"Resource check: Memory={memory_gb:.2f}GB/{max_memory_gb}GB, "
        f"CPU={cpu_cores_used:.2f}/{max_cpu_cores} cores"
    )
