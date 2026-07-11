"""
Logging and resource monitoring utilities.
"""
import os
import time
import resource
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ResourceSnapshot:
    cpu_time: float
    memory_mb: float
    timestamp: float

@dataclass
class HeuristicTimer:
    name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
    
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        return (self.end_time or time.time()) - self.start_time

def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_current_resource_snapshot() -> ResourceSnapshot:
    """Get current CPU time and memory usage."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return ResourceSnapshot(
        cpu_time=usage.ru_utime + usage.ru_stime,
        memory_mb=usage.ru_maxrss / 1024, # Convert KB to MB (Linux)
        timestamp=time.time()
    )

@contextmanager
def measure_heuristic(name: str):
    """Context manager to measure heuristic execution time."""
    timer = HeuristicTimer(name)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
        logger = logging.getLogger(__name__)
        logger.info(f"Heuristic '{name}' took {timer.elapsed():.4f}s")
