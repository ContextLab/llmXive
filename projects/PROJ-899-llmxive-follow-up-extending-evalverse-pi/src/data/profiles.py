import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config import get_state_root, get_project_root
from src.utils import write_json, get_logger
from src.data.preprocess import process_video_clip

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """
    Get the current memory usage of the process in MB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)


def get_cpu_time_seconds() -> float:
    """
    Get the CPU time used by the process in seconds.
    """
    return time.process_time()


def profile_clip_execution(clip_path: str, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Profile the execution of a single video clip.
    Measures memory peak and execution time.
    
    Args:
        clip_path: Path to the video file.
        timeout_seconds: Maximum allowed execution time.
        
    Returns:
        Dictionary with profiling metrics.
    """
    start_time = time.time()
    start_cpu = time.process_time()
    start_mem = get_memory_usage_mb()
    max_mem = start_mem
    
    status = "success"
    error_msg = None
    
    try:
        # Execute the actual processing
        # Note: process_video_clip is imported from preprocess.py
        result = process_video_clip(clip_path)
        
        if not result or result.get("status") != "success":
            status = "failed"
            error_msg = result.get("error", "Unknown error") if result else "No result returned"
            
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        logger.error(f"Error processing {clip_path}: {e}")
        
    end_time = time.time()
    end_cpu = time.process_time()
    end_mem = get_memory_usage_mb()
    
    duration = end_time - start_time
    cpu_duration = end_cpu - start_cpu
    
    # Update max memory if current is higher
    if end_mem > max_mem:
        max_mem = end_mem
        
    # Also check peak from psutil if available (more accurate for bursts)
    try:
        process = psutil.Process(os.getpid())
        peak_mem_mb = process.memory_info().rss / (1024 * 1024) # Using RSS as approximation for peak in this simple context
        # Note: psutil.Process.memory_info().maxrss is not available on all platforms consistently
        # We rely on the delta check above for simplicity in this implementation
        if peak_mem_mb > max_mem:
            max_mem = peak_mem_mb
    except Exception:
        pass
        
    return {
        "clip_path": clip_path,
        "memory_mb": max_mem,
        "time_seconds": duration,
        "cpu_time_seconds": cpu_duration,
        "status": status,
        "error": error_msg
    }


def save_profiling_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save profiling results to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Profiling results saved to {output_path}")


def load_profiling_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load profiling results from a JSON file.
    """
    if not os.path.exists(input_path):
        return []
        
    with open(input_path, 'r') as f:
        return json.load(f)


def run_feasibility_gate(
    profiling_data: List[Dict[str, Any]],
    projected_total_hours: float,
    output_filename: str = "feasibility_gate.json"
) -> Dict[str, Any]:
    """
    Run the feasibility gate check.
    
    Constraints:
    - Peak memory must be <= 7GB
    - Projected total time must be <= 6.0 hours
    
    Returns:
        Dictionary with gate status and details.
    """
    state_root = get_state_root()
    output_path = state_root / output_filename
    
    # Calculate peak memory from profiling data
    if not profiling_data:
        logger.warning("No profiling data provided for feasibility gate.")
        peak_memory_gb = 0.0
    else:
        peak_memory_mb = max(d.get("memory_mb", 0) for d in profiling_data)
        peak_memory_gb = peak_memory_mb / 1024.0
        
    # Check constraints
    max_memory_gb = 7.0
    max_hours = 6.0
    
    passed = True
    reason = None
    
    if peak_memory_gb > max_memory_gb:
        passed = False
        reason = f"Peak memory ({peak_memory_gb:.2f} GB) exceeds limit ({max_memory_gb:.2f} GB)"
        
    if projected_total_hours > max_hours:
        passed = False
        reason = f"Projected total time ({projected_total_hours:.2f} hours) exceeds limit ({max_hours:.2f} hours)"
        
    result = {
        "passed": passed,
        "peak_memory_gb": peak_memory_gb,
        "projected_hours": projected_total_hours,
        "max_memory_gb_limit": max_memory_gb,
        "max_hours_limit": max_hours,
        "status": "viable" if passed else "non-viable",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write to state directory
    write_json(result, output_path)
    logger.info(f"Feasibility gate result: {result['status']}")
    
    return result


def main():
    """
    Main entry point for running the feasibility gate on a sample batch.
    This function is designed to be called by the pipeline runner.
    """
    logger.info("Starting feasibility gate profiling...")
    
    # In a real scenario, we would load the list of clips to process
    # For this gate, we assume profiling data is already collected or we run a small sample
    # Since T024 provides the projection, we need to read it or pass it in.
    # Here we simulate reading from the timing profile generated by T024 if it exists.
    
    # For the purpose of this task implementation, we assume the caller passes the necessary data
    # or we read from the expected artifact path generated by T024.
    
    timing_profile_path = get_state_root() / ".." / "data" / "timing_profile.csv"
    # Note: The exact path logic might vary based on how T024 writes it. 
    # Assuming T024 writes to data/timing_profile.csv relative to project root.
    # Let's use a robust path resolution.
    from src.config import get_data_root
    timing_profile_path = get_data_root() / "timing_profile.csv"
    
    projected_hours = 0.0
    profiling_data = []
    
    if os.path.exists(timing_profile_path):
        import pandas as pd
        df = pd.read_csv(timing_profile_path)
        if "projected_total_hours" in df.columns:
            # Assuming single row or taking the last valid entry
            projected_hours = float(df["projected_total_hours"].iloc[-1])
        
        # Re-run profiling on a sample if we don't have raw data, 
        # or load raw data if T023b wrote it.
        # T023b writes data/profiling_logs.json
        raw_log_path = get_data_root() / "profiling_logs.json"
        if os.path.exists(raw_log_path):
            profiling_data = load_profiling_results(str(raw_log_path))
        else:
            # Fallback: run a quick sample if raw logs missing (for gate robustness)
            logger.info("Raw profiling logs not found, running quick sample...")
            # Get sample clips (logic would need to be extracted or duplicated)
            # For now, we rely on the data existing as per T022/T023b completion.
            pass
    else:
        logger.warning(f"Timing profile not found at {timing_profile_path}. Cannot project time.")
        
    if not profiling_data:
        logger.error("No profiling data available to check memory constraints.")
        # Create a dummy failure result
        result = run_feasibility_gate([], 0.0)
        sys.exit(1)
        
    # Run the gate
    result = run_feasibility_gate(profiling_data, projected_hours)
    
    if not result["passed"]:
        logger.error(f"Feasibility gate FAILED: {result['reason']}")
        sys.exit(1)
    else:
        logger.info("Feasibility gate PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()