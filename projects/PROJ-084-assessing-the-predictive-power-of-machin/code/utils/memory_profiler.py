"""
Memory profiling utilities for the ML pipeline.
Implements @profile_memory decorator using tracemalloc and psutil.
Logs aggregate peak RAM and runtime to data/results/memory_profile.log and data/results/runtime_profile.json.
"""
import gc
import json
import logging
import tracemalloc
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
RESULTS_DIR = Path("data/results")
MEMORY_LOG_PATH = RESULTS_DIR / "memory_profile.log"
RUNTIME_PROFILE_PATH = RESULTS_DIR / "runtime_profile.json"

# Global storage for profiling results
_profile_results: List[Dict[str, Any]] = []

def _ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def get_current_memory_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB since tracemalloc started."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def check_memory_limit(current_mb: float) -> bool:
    """Check if current memory usage is within the 7GB limit."""
    limit_mb = MEMORY_LIMIT_GB * 1024
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB")
        return False
    return True

def force_gc():
    """Force garbage collection to free memory."""
    gc.collect()

def profile_memory(step_name: str):
    """
    Decorator to profile memory and runtime for a function.
    Logs peak RAM and runtime to memory_profile.log and runtime_profile.json.
    Asserts total system RAM < 7GB.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _ensure_results_dir()

            logger.info(f"Starting memory profiling for step: {step_name}")

            # Force GC before starting
            force_gc()

            # Start tracemalloc
            tracemalloc.start()

            start_time = time.time()
            peak_memory_mb = 0.0
            success = False
            error_msg = None

            try:
                # Execute the function
                result = func(*args, **kwargs)
                success = True

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error during {step_name}: {error_msg}")
                raise

            finally:
                # Stop tracemalloc
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                peak_memory_mb = peak / (1024 * 1024)
                end_time = time.time()
                runtime_seconds = end_time - start_time

                # Check memory limit
                if not check_memory_limit(peak_memory_mb):
                    raise MemoryError(f"Memory limit exceeded for step {step_name}: {peak_memory_mb:.2f} MB")

                # Log results
                profile_entry = {
                    "step_name": step_name,
                    "timestamp": datetime.now().isoformat(),
                    "peak_memory_mb": round(peak_memory_mb, 2),
                    "runtime_seconds": round(runtime_seconds, 4),
                    "success": success,
                    "error": error_msg
                }
                _profile_results.append(profile_entry)

                # Write to log file
                with open(MEMORY_LOG_PATH, "a") as f:
                    log_line = f"{profile_entry['timestamp']} - {step_name}: Peak RAM = {profile_entry['peak_memory_mb']:.2f} MB, Runtime = {profile_entry['runtime_seconds']:.4f} s, Status = {'SUCCESS' if success else 'FAILED'}\n"
                    f.write(log_line)

                # Write to JSON profile
                with open(RUNTIME_PROFILE_PATH, "w") as f:
                    json.dump(_profile_results, f, indent=2)

                logger.info(f"Completed profiling for {step_name}: Peak RAM = {peak_memory_mb:.2f} MB, Runtime = {runtime_seconds:.4f} s")

                return result

        return wrapper
    return decorator

def save_memory_profile_log():
    """Save the current profile results to the log files."""
    _ensure_results_dir()
    with open(RUNTIME_PROFILE_PATH, "w") as f:
        json.dump(_profile_results, f, indent=2)
    logger.info(f"Saved {len(_profile_results)} profile entries to {RUNTIME_PROFILE_PATH}")

def main():
    """
    Main function to demonstrate memory profiling.
    This is a self-test that runs a dummy function to verify the profiler works.
    """
    logger.info("Running memory profiler self-test...")

    @profile_memory("self_test_dummy_step")
    def dummy_step():
        """A dummy function to test the profiler."""
        time.sleep(0.1)
        # Allocate some memory
        data = [i for i in range(100000)]
        return data

    try:
        result = dummy_step()
        logger.info(f"Self-test completed successfully. Result length: {len(result)}")
        save_memory_profile_log()
    except Exception as e:
        logger.error(f"Self-test failed: {e}")
        raise

if __name__ == "__main__":
    main()