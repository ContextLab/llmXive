"""
Runtime profiling and logging utilities for the llmXive science pipeline.

This module provides decorators and context managers to monitor execution time
and identify bottlenecks across the pipeline scripts.
"""
import os
import sys
import time
import logging
import cProfile
import pstats
import io
from functools import wraps
from typing import Callable, Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

# Import existing setup_logging to ensure consistent log configuration
from utils import setup_logging

# Configure logger
logger = logging.getLogger(__name__)

# Global profiling storage
_profile_data: List[Dict[str, Any]] = []

def _get_execution_id() -> str:
    """Generate a unique execution ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile a function's execution time and log results.
    
    Args:
        func: The function to profile.
        
    Returns:
        The wrapped function with profiling enabled.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Log the execution time
            logger.info(
                f"FUNCTION_COMPLETE: {module_name}.{func_name} "
                f"duration={duration:.4f}s args={len(args)} kwargs={len(kwargs)}"
            )
            
            # Store profiling data
            _profile_data.append({
                "execution_id": _get_execution_id(),
                "function": f"{module_name}.{func_name}",
                "duration_seconds": duration,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return result
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            logger.error(
                f"FUNCTION_FAILED: {module_name}.{func_name} "
                f"duration={duration:.4f}s error={str(e)}",
                exc_info=True
            )
            
            _profile_data.append({
                "execution_id": _get_execution_id(),
                "function": f"{module_name}.{func_name}",
                "duration_seconds": duration,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            raise
    return wrapper

@contextmanager
def profile_block(block_name: str):
    """
    Context manager to profile a block of code.
    
    Args:
        block_name: A descriptive name for the code block.
        
    Example:
        with profile_block("data_loading"):
            df = load_data()
    """
    start_time = time.perf_counter()
    try:
        yield
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        logger.info(
            f"BLOCK_COMPLETE: {block_name} duration={duration:.4f}s"
        )
        
        _profile_data.append({
            "execution_id": _get_execution_id(),
            "block": block_name,
            "duration_seconds": duration,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        logger.error(
            f"BLOCK_FAILED: {block_name} duration={duration:.4f}s error={str(e)}"
        )
        
        _profile_data.append({
            "execution_id": _get_execution_id(),
            "block": block_name,
            "duration_seconds": duration,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise

def run_cprofile(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Run a function with detailed cProfile analysis.
    
    Args:
        func: The function to profile.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        A dictionary containing profile statistics.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()
    
    # Create a string buffer to hold stats
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)  # Print top 20 functions
    
    output = s.getvalue()
    
    # Log the top bottlenecks
    logger.info(f"PROFILE_DETAILED: {func.__name__}\n{output}")
    
    return {
        "function": func.__name__,
        "top_bottlenecks": output,
        "timestamp": datetime.now().isoformat()
    }

def save_profile_report(output_path: Optional[str] = None) -> str:
    """
    Save all collected profiling data to a JSON file.
    
    Args:
        output_path: Optional path to save the report. Defaults to 
                    'data/processed/profile_report.json'.
                    
    Returns:
        The path where the report was saved.
    """
    if output_path is None:
        output_path = "data/processed/profile_report.json"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        "total_executions": len(_profile_data),
        "total_duration_seconds": sum(
            item.get("duration_seconds", 0) for item in _profile_data
        ),
        "successful": sum(1 for item in _profile_data if item.get("status") == "success"),
        "failed": sum(1 for item in _profile_data if item.get("status") == "failed"),
        "timestamp": datetime.now().isoformat(),
        "executions": _profile_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"PROFILE_REPORT_SAVED: {output_path} (total executions: {len(_profile_data)})")
    return output_path

def identify_bottlenecks(threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
    """
    Identify functions/blocks that exceeded the duration threshold.
    
    Args:
        threshold_seconds: Duration threshold in seconds to flag as bottleneck.
        
    Returns:
        List of profiling entries that exceeded the threshold.
    """
    bottlenecks = [
        item for item in _profile_data
        if item.get("duration_seconds", 0) > threshold_seconds
    ]
    
    if bottlenecks:
        logger.warning(
            f"BOTTLENECKS_DETECTED: {len(bottlenecks)} operations exceeded "
            f"{threshold_seconds}s threshold"
        )
        for bn in bottlenecks:
            logger.warning(
                f"  - {bn.get('function') or bn.get('block')}: "
                f"{bn.get('duration_seconds', 0):.4f}s"
            )
    
    return bottlenecks

def reset_profile_data():
    """Clear all collected profiling data."""
    global _profile_data
    _profile_data = []
    logger.info("PROFILE_DATA_RESET")

# Main entry point for standalone execution
def main():
    """
    Standalone execution to demonstrate profiling capabilities.
    This script can be run to initialize the profiler or generate a sample report.
    """
    # Setup logging
    setup_logging()
    
    logger.info("PROFILER_MODULE_INITIALIZED")
    
    # Example usage demonstration
    @profile_function
    def example_slow_function():
        time.sleep(0.5)
        return "done"
    
    with profile_block("example_block"):
        result = example_slow_function()
        logger.info(f"Example result: {result}")
    
    # Save report
    report_path = save_profile_report()
    logger.info(f"Profile report saved to: {report_path}")
    
    # Identify bottlenecks
    bottlenecks = identify_bottlenecks(threshold_seconds=0.1)
    if bottlenecks:
        logger.info(f"Found {len(bottlenecks)} bottlenecks")
    
    print(f"Profiler initialized. Report saved to: {report_path}")

if __name__ == "__main__":
    main()
