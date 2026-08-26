import time
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

_timing_results: Dict[str, float] = {}

def get_elapsed_time(start_time: float) -> float:
    return time.perf_counter() - start_time

@contextmanager
def cpu_timer(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        _timing_results[name] = _timing_results.get(name, 0.0) + elapsed
        logger.info(f"CPU Timer [{name}]: {elapsed:.4f}s")

def profile_function(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"Profiled [{func.__name__}]: {elapsed:.4f}s")
        return result
    return wrapper

def get_timing_report() -> Dict[str, float]:
    return _timing_results.copy()

def reset_timing_results() -> None:
    _timing_results.clear()

def save_timing_results(output_path: Path) -> None:
    with open(output_path, "w") as f:
        json.dump(_timing_results, f, indent=2)
    logger.info(f"Timing results saved to {output_path}")
