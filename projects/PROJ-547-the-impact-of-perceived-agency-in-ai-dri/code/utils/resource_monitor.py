from __future__ import annotations

import os
import psutil
from logging.pipeline_logger import get_logger
from utils.error_handler import PipelineError

DEFAULT_MEMORY_LIMIT_GB = 6.0
DEFAULT_CPU_LIMIT = 2

def enforce_limits(
    memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB,
    cpu_limit: int = DEFAULT_CPU_LIMIT,
    *,
    memory_usage_bytes: int | None = None,
    cpu_count: int | None = None,
) -> None:
    """
    Enforce resource usage limits for the pipeline.

    Parameters
    ----------
    memory_limit_gb : float
        Maximum allowed memory usage in gigabytes.
    cpu_limit : int
        Maximum allowed number of CPU cores.
    memory_usage_bytes : int | None, optional
        Override for current memory usage (RSS) in bytes. If None, the function
        queries the current process via ``psutil``.
    cpu_count : int | None, optional
        Override for the number of CPU cores detected. If None, the function
        uses ``os.cpu_count()``.

    Raises
    ------
    PipelineError
        If either the memory usage or CPU core count exceeds the supplied limits.
    """
    logger = get_logger(__name__)

    # Determine current memory usage
    if memory_usage_bytes is None:
        process = psutil.Process()
        memory_usage_bytes = process.memory_info().rss

    # Determine current CPU core count
    if cpu_count is None:
        cpu_count = os.cpu_count() or 0

    mem_gb = memory_usage_bytes / (1024 ** 3)

    if mem_gb > memory_limit_gb:
        msg = (
            f"Memory usage {mem_gb:.2f} GB exceeds limit of {memory_limit_gb} GB. "
            "Aborting pipeline."
        )
        logger.error(msg)
        raise PipelineError(msg)

    if cpu_count > cpu_limit:
        msg = (
            f"CPU core count {cpu_count} exceeds limit of {cpu_limit} cores. "
            "Aborting pipeline."
        )
        logger.error(msg)
        raise PipelineError(msg)

    logger.info(
        f"Resource usage within limits: {mem_gb:.2f} GB memory, {cpu_count} CPU cores."
    )
