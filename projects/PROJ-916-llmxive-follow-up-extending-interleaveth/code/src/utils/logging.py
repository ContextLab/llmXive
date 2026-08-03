"""
Logging infrastructure for llmXive pipeline.

Tracks RAM usage via tracemalloc and execution time per step.
"""
import logging
import sys
import time
import tracemalloc
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional, Dict, Any

# Configure root logger for the project
# Format: [timestamp] [level] [name] message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a project-specific logger
logger = logging.getLogger("llmXive")


class MemorySnapshot:
    """Stores a snapshot of memory usage."""
    def __init__(self):
        self.current: int = 0
        self.peak: int = 0
        self.timestamp: datetime = datetime.now()

    def update(self):
        """Update current and peak memory usage."""
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            self.current = current
            self.peak = peak
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "current_bytes": self.current,
            "peak_bytes": self.peak,
            "current_mb": self.current / (1024 * 1024),
            "peak_mb": self.peak / (1024 * 1024)
        }


class StepTimer:
    """Context manager to track execution time of a step."""
    def __init__(self, step_name: str, logger_instance: logging.Logger = logger):
        self.step_name = step_name
        self.logger = logger_instance
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self) -> "StepTimer":
        self.start_time = time.perf_counter()
        self.logger.info(f"Starting step: {self.step_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed step: {self.step_name} in {self.duration:.4f}s")
        else:
            self.logger.error(f"Failed step: {self.step_name} after {self.duration:.4f}s with {exc_type.__name__}: {exc_val}")
        
        return False  # Do not suppress exceptions


class RAMTracker:
    """Context manager to track RAM usage during a block of code."""
    def __init__(self, step_name: str, logger_instance: logging.Logger = logger):
        self.step_name = step_name
        self.logger = logger_instance
        self.snapshot_start: Optional[MemorySnapshot] = None
        self.snapshot_end: Optional[MemorySnapshot] = None

    def __enter__(self) -> "RAMTracker":
        self.snapshot_start = MemorySnapshot()
        self.snapshot_start.update()
        self.logger.info(f"RAM check-in at start of {self.step_name}: {self.snapshot_start.current_mb:.2f} MB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.snapshot_end = MemorySnapshot()
        self.snapshot_end.update()
        
        delta = self.snapshot_end.current - self.snapshot_start.current
        delta_mb = delta / (1024 * 1024)
        
        status = "allocated" if delta > 0 else "freed"
        self.logger.info(
            f"RAM check-out at end of {self.step_name}: "
            f"start={self.snapshot_start.current_mb:.2f} MB, "
            f"end={self.snapshot_end.current_mb:.2f} MB, "
            f"delta={delta_mb:.2f} MB ({status})"
        )
        return False


@contextmanager
def track_step(step_name: str) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager that tracks both time and RAM for a specific step.
    
    Yields a dictionary containing the step metrics.
    """
    metrics = {
        "step_name": step_name,
        "start_time": datetime.now().isoformat(),
        "duration_s": 0.0,
        "ram_start_mb": 0.0,
        "ram_end_mb": 0.0,
        "ram_delta_mb": 0.0,
        "success": False
    }

    with StepTimer(step_name):
        with RAMTracker(step_name) as ram_ctx:
            try:
                yield metrics
                metrics["success"] = True
            except Exception as e:
                logger.error(f"Exception in step {step_name}: {e}")
                raise
            finally:
                # Capture final metrics
                if ram_ctx.snapshot_start:
                    metrics["ram_start_mb"] = ram_ctx.snapshot_start.current_mb
                if ram_ctx.snapshot_end:
                    metrics["ram_end_mb"] = ram_ctx.snapshot_end.current_mb
                    metrics["ram_delta_mb"] = metrics["ram_end_mb"] - metrics["ram_start_mb"]

def start_tracing():
    """Start tracemalloc if not already running."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("tracemalloc started for memory tracking.")

def stop_tracing():
    """Stop tracemalloc and print statistics if running."""
    if tracemalloc.is_tracing():
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        logger.info("tracemalloc stopped. Top 5 memory allocations:")
        for stat in top_stats[:5]:
            logger.info(stat)
        tracemalloc.stop()
    else:
        logger.warning("tracemalloc was not running.")

# Initialize tracing on import to ensure we catch all allocations
start_tracing()
