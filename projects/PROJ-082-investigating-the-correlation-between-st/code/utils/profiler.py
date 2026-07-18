"""
Profiling utilities for the llmXive pipeline.
Measures runtime, memory, and identifies bottlenecks to ensure CI execution < 15 mins.
"""
import cProfile
import pstats
import io
import sys
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps

from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

# Type hint for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

def profile_pipeline_entrypoint(func: F) -> F:
    """
    Decorator to profile a pipeline entry point function.
    Records CPU time, wall time, and saves a profile report.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Start CPU profiling
        pr = cProfile.Profile()
        pr.enable()

        # Start memory profiling
        tracemalloc.start()

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Pipeline execution failed during profiling: {e}")
            raise
        finally:
            end_time = time.perf_counter()
            pr.disable()
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        # Calculate stats
        total_time = end_time - start_time
        elapsed_minutes = total_time / 60.0

        # Check against CI limit (15 minutes)
        CI_LIMIT_MINUTES = 15.0
        if elapsed_minutes > CI_LIMIT_MINUTES:
            logger.warning(
                f"Pipeline execution exceeded CI limit of {CI_LIMIT_MINUTES} minutes. "
                f"Actual time: {elapsed_minutes:.2f} minutes."
            )
        else:
            logger.info(
                f"Pipeline execution completed within CI limit. "
                f"Time: {elapsed_minutes:.2f} minutes."
            )

        # Save profile results
        profile_data = {
            "function_name": func.__name__,
            "total_time_seconds": total_time,
            "elapsed_minutes": elapsed_minutes,
            "peak_memory_mb": peak / (1024 * 1024),
            "current_memory_mb": current / (1024 * 1024),
            "ci_limit_minutes": CI_LIMIT_MINUTES,
            "status": "PASS" if elapsed_minutes <= CI_LIMIT_MINUTES else "FAIL",
            "top_10_functions": []
        }

        # Extract top 10 functions from stats
        s = io.StringIO()
        stats = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        stats.print_stats(10)
        profile_data["top_10_functions"] = s.getvalue()

        # Save to file
        output_path = Path("data/logs/profile_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)
        
        logger.info(f"Profile report saved to {output_path}")
        
        return result
    
    return wrapper  # type: ignore

def save_profile_results(pr: cProfile.Profile, output_path: str, top_n: int = 20) -> None:
    """
    Saves the results of a cProfile object to a JSON file.
    """
    s = io.StringIO()
    stats = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    stats.print_stats(top_n)
    
    profile_data = {
        "top_functions": s.getvalue()
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2)
    
    logger.info(f"Profile results saved to {output_path}")

def run_profiler(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Runs a function under the profiler and returns the metrics dictionary.
    """
    pr = cProfile.Profile()
    pr.enable()
    
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    
    pr.disable()
    
    s = io.StringIO()
    stats = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    stats.print_stats(20)
    
    return {
        "duration_seconds": end - start,
        "top_stats": s.getvalue()
    }

def main() -> None:
    """
    CLI entry point to run the profiler on the main pipeline.
    Usage: python code/utils/profiler.py
    """
    logger.info("Starting profiler for main pipeline...")
    
    # Import here to avoid circular imports if this module is imported elsewhere
    try:
        from main import run_pipeline
    except ImportError:
        logger.error("Could not import run_pipeline from main. Ensure code/ is in PYTHONPATH.")
        sys.exit(1)

    try:
        # Run the pipeline under the decorator logic manually or via wrapper
        # We'll invoke the decorated version if possible, or wrap it here
        # Since run_pipeline is likely the entry point, we wrap it
        wrapped_pipeline = profile_pipeline_entrypoint(run_pipeline)
        wrapped_pipeline()
    except Exception as e:
        logger.error(f"Profiling run failed: {e}")
        sys.exit(1)

    logger.info("Profiling complete. Check data/logs/profile_report.json")

if __name__ == "__main__":
    main()
