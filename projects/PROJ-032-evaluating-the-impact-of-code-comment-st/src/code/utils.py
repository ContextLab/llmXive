import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, List, Any, Optional
import threading
import psutil

def configure_logging(log_path: str = "logs/pipeline.log") -> logging.Logger:
    """
    Set up file and console handlers with INFO/ERROR levels.
    Returns the root logger configured with these handlers.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class BatchIterator(Iterator):
    """
    Iterator that enforces max concurrent operations using a semaphore.
    """
    def __init__(self, items: List[Any], max_concurrent: int = 10):
        self.items = items
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._index = 0
        self._lock = threading.Lock()

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> Any:
        with self._lock:
            if self._index >= len(self.items):
                raise StopIteration
            item = self.items[self._index]
            self._index += 1

        self._semaphore.acquire()
        return item

    def release(self):
        """Call this after processing an item to release the semaphore."""
        self._semaphore.release()


class MemoryMonitor:
    """
    Monitors system memory usage using psutil.
    Raises MemoryError if usage exceeds a specified limit.
    """
    def __init__(self, limit_gb: float = 7.0):
        """
        Initialize the memory monitor.

        Args:
            limit_gb: The maximum allowed memory usage in gigabytes.
        """
        self.limit_bytes = limit_gb * (1024 ** 3)
        self.process = psutil.Process(os.getpid())

    def check_limit(self, limit_gb: Optional[float] = None) -> bool:
        """
        Check if current memory usage exceeds the limit.

        Args:
            limit_gb: Optional override for the memory limit in GB.

        Returns:
            True if within limits.

        Raises:
            MemoryError: If memory usage exceeds the limit.
        """
        if limit_gb is not None:
            current_limit = limit_gb * (1024 ** 3)
        else:
            current_limit = self.limit_bytes

        # Get current memory usage in bytes
        current_mem = self.process.memory_info().rss

        if current_mem > current_limit:
            raise MemoryError(
                f"Memory usage {current_mem / (1024**3):.2f}GB exceeds limit of {current_limit / (1024**3):.2f}GB"
            )
        
        return True

    def get_usage_gb(self) -> float:
        """Return current memory usage in GB."""
        return self.process.memory_info().rss / (1024 ** 3)


class CommitSampler:
    """
    Selects representative commits for static analysis.
    """
    def __init__(self):
        pass

    def sample_commits(self, commits: List[str], n: int = 10) -> List[str]:
        """
        Select n representative commits from the list.
        
        Args:
            commits: List of commit hashes or identifiers.
            n: Number of commits to select.
            
        Returns:
            List of selected commit hashes.
        """
        if not commits:
            return []
        
        if n >= len(commits):
            return commits
        
        # Simple random sampling without replacement
        import random
        return random.sample(commits, n)


def generate_manual_labels():
    """
    Placeholder for manual label generation.
    This function is a stub and should be implemented later.
    """
    pass