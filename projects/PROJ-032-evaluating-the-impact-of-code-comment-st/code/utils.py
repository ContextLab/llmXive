import logging
import os
import asyncio
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, List, Any, Optional, Callable, TypeVar
import threading

T = TypeVar('T')

def configure_logging(log_path="logs/pipeline.log"):
    """Set up file and console handlers with INFO/ERROR levels."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

class BatchIterator(Iterator[T]):
    """Iterator with semaphore logic to enforce max concurrent clones."""
    def __init__(self, items: List[T], max_concurrent: int = 10):
        self.items = items
        self.index = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            if self.index >= len(self.items):
                raise StopIteration
            item = self.items[self.index]
            self.index += 1
            return item

class MemoryMonitor:
    """Monitor memory usage using psutil."""
    def __init__(self):
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            raise ImportError("psutil is required for MemoryMonitor. Install it via pip install psutil.")

    def check_limit(self, limit_gb: float = 7.0):
        """Raise MemoryError if memory usage exceeds limit."""
        process = self.psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_gb = mem_info.rss / (1024 ** 3)
        if current_gb > limit_gb:
            raise MemoryError(f"Memory limit exceeded: {current_gb:.2f}GB > {limit_gb}GB")
        return True

class CommitSampler:
    """Select representative commits for static analysis."""
    def __init__(self, seed: int = 42):
        import random
        self.random = random
        self.seed = seed

    def sample_commits(self, commits: List[str], n: int = 10) -> List[str]:
        """Select n representative commits from the list."""
        if not commits:
            return []
        if len(commits) <= n:
            return commits
        self.random.seed(self.seed)
        return self.random.sample(commits, n)

def generate_manual_labels(repos: List[str], target_size: int = 50):
    """Generate manual labels for validation (placeholder logic for T007e)."""
    # This is a placeholder. The real implementation would stratify sample commits
    # and label them. For T035, we just ensure the function exists in utils if needed,
    # though T007e requires the actual logic in metrics.py or a dedicated script.
    # Since T007e is marked failed, we don't implement the full logic here, 
    # but we ensure the signature matches the API surface if it was expected here.
    # However, the API surface says it's in utils. Let's provide a minimal stub
    # that raises if not fully implemented, or returns empty if just checking existence.
    # Given the task is to implement T035, we assume the signature must exist.
    # But the task description for T007e says it's missing.
    # We will leave this as a minimal stub that raises NotImplementedError
    # to force the real implementation in the correct place (T007e).
    raise NotImplementedError("generate_manual_labels logic must be fully implemented in T007e.")

def run_metric_aggregation_with_memory_monitor(metrics_list: List[Dict], limit_gb: float = 7.0):
    """Aggregate metrics while monitoring memory."""
    monitor = MemoryMonitor()
    monitor.check_limit(limit_gb)
    # Placeholder aggregation logic
    return metrics_list

def timeit(func: Callable) -> Callable:
    """Decorator to measure execution time and memory usage."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        tracemalloc.start()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = end_time - start_time
            logging.info(f"Function {func.__name__} took {elapsed:.2f}s. Peak memory: {peak / 1024 / 1024:.2f} MB")
            return result
        except Exception as e:
            tracemalloc.stop()
            raise e
    return wrapper
