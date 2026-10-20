"""
Resource Guard
---------------
Simple guard that checks the current RAM usage (via ``psutil``) and
raises an exception if the process exceeds a user‑defined limit.
The function is used by the fetcher before starting a large download
to avoid exhausting the runner’s memory.
"""

import logging
import sys

import psutil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def enforce_memory_limit(max_ram_gb: int = 6) -> None:
    """
    Abort the program if the current process is using more than
    ``max_ram_gb`` gigabytes of RAM.  The check is performed *before*
    a heavyweight operation (e.g., a dataset download) begins.

    Raises
    ------
    RuntimeError
        If the memory usage exceeds the specified limit.
    """
    process = psutil.Process()
    mem_bytes = process.memory_info().rss
    mem_gb = mem_bytes / (1024 ** 3)
    if mem_gb > max_ram_gb:
        raise RuntimeError(
            f"Memory usage ({mem_gb:.2f} GiB) exceeds the allowed limit of {max_ram_gb} GiB."
        )
    logger.debug(f"Current memory usage: {mem_gb:.2f} GiB (limit {max_ram_gb} GiB)")
