import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional

from src.utils import get_logger, write_json, ensure_directories
from src.config import get_processed_data_dir, get_data_root

def get_memory_usage_mb(process: psutil.Process) -> float:
    """Returns current memory usage in MB."""
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_time_seconds() -> float:
    """Returns CPU time used by the current process."""
    return time.process_time()

def profile_clip_execution(clip_id: str, func: callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Profiles the execution of a function for a specific clip.
    Returns a dictionary with timing and memory stats.
    """
    logger = get_logger()
    process = psutil.Process(os.getpid())
    start_mem = get_memory_usage_mb(process)
    start_time = time.time()
    cpu_start = time.process_time()
    
    status = "success"
    error_msg = None
    
    try:
        func(*args, **kwargs)
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        logger.error(f"Error profiling clip {clip_id}: {e}")
    finally:
        end_time = time.time()
        cpu_end = time.process_time()
        end_mem = get_memory_usage_mb(process)
        
        elapsed_time = end_time - start_time
        cpu_time = cpu_end - cpu_start
        peak_mem = max(start_mem, end_mem) # Approximate peak
        
        return {
            "clip_id": clip_id,
            "cpu_time_sec": cpu_time,
            "peak_memory_mb": peak_mem,
            "status": status,
            "error": error_msg
        }

def save_profiling_results(results: List[Dict[str, Any]], output_file: Optional[str] = None):
    """Saves profiling results to a JSON file."""
    if output_file is None:
        output_file = get_processed_data_dir() / "profiling_logs.json"
    
    ensure_directories()
    write_json(results, output_file)
    get_logger().info(f"Saved profiling results to {output_file}")

def load_profiling_results(input_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads profiling results from a JSON file."""
    if input_file is None:
        input_file = get_processed_data_dir() / "profiling_logs.json"
    
    if not os.path.exists(input_file):
        get_logger().error(f"Profiling results not found at {input_file}")
        return []
    
    with open(input_file, 'r') as f:
        return json.load(f)

def run_feasibility_gate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Runs the feasibility gate based on profiling results.
    Checks if peak_memory_mb > 7GB and projected time > 6h.
    Returns a status dictionary.
    """
    logger = get_logger()
    
    if not results:
        logger.error("No profiling results to gate.")
        return {"status": "fail", "reason": "no_results"}
    
    # Calculate stats
    peak_memory_mb = max(r.get('peak_memory_mb', 0) for r in results if r.get('status') == 'success')
    successful_times = [r.get('cpu_time_sec', 0) for r in results if r.get('status') == 'success']
    
    if not successful_times:
        logger.error("No successful clips to calculate time.")
        return {"status": "fail", "reason": "no_successful_clips"}
    
    mean_time = sum(successful_times) / len(successful_times)
    total_clips = 10000 # Assumed target
    projected_hours = (mean_time * total_clips) / 3600
    
    logger.info(f"Peak Memory: {peak_memory_mb:.2f} MB")
    logger.info(f"Mean Time per Clip: {mean_time:.4f} sec")
    logger.info(f"Projected Total Time (10k clips): {projected_hours:.2f} hours")
    
    status = "pass"
    reasons = []
    
    if peak_memory_mb > 7168: # 7GB
        status = "fail"
        reasons.append(f"Peak memory {peak_memory_mb:.2f} MB exceeds 7GB limit.")
    
    if projected_hours > 6.0:
        status = "fail"
        reasons.append(f"Projected time {projected_hours:.2f} hours exceeds 6h limit.")
    
    result = {
        "status": status,
        "peak_memory_mb": peak_memory_mb,
        "mean_time_sec": mean_time,
        "projected_hours": projected_hours,
        "reasons": reasons
    }
    
    if status == "fail":
        logger.error(f"Feasibility gate FAILED: {'; '.join(reasons)}")
        return result
    
    logger.info("Feasibility gate PASSED")
    return result

def main():
    """Entry point for profiling module."""
    try:
        get_logger().info("Profiles module loaded.")
        return 0
    except Exception as e:
        get_logger().error(f"Profiles module error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
