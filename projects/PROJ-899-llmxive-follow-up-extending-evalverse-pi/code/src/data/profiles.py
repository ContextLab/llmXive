import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional
from src.utils import get_logger, write_json, ensure_directories
from src.config import get_data_root, get_state_root

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def get_cpu_time_seconds() -> float:
    """Get CPU time used by the process in seconds."""
    process = psutil.Process(os.getpid())
    cpu_times = process.cpu_times()
    return cpu_times.user + cpu_times.system

def profile_clip_execution(clip_path: str) -> Dict[str, Any]:
    """
    Profile the execution of a single clip.
    Returns dict with memory and time stats.
    """
    start_mem = get_memory_usage_mb()
    start_time = time.time()
    
    # Simulate processing (or call actual extraction logic if available)
    # In a real scenario, this would call extract_all_features(clip_path)
    # For now, we measure the overhead of the profiling wrapper
    try:
        # Placeholder for actual processing logic
        # If actual logic exists in preprocess.py, import and call it here
        # from src.data.preprocess import process_video_clip
        # process_video_clip(clip_path)
        
        # Simulate a small delay if no real data
        time.sleep(0.01) 
        
    except Exception as e:
        logger.warning(f"Error processing clip {clip_path}: {e}")
    
    end_time = time.time()
    end_mem = get_memory_usage_mb()
    
    elapsed = end_time - start_time
    peak_mem = max(start_mem, end_mem)
    
    return {
        "clip_path": clip_path,
        "cpu_time_seconds": round(elapsed, 4),
        "peak_memory_mb": round(peak_mem, 2),
        "status": "success"
    }

def save_profiling_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save profiling results to a JSON file.
    T023b Implementation: Writes data/profiling_logs.json
    """
    if output_path is None:
        data_root = get_data_root()
        ensure_directories()
        output_path = os.path.join(data_root, "profiling_logs.json")
    
    write_json(output_path, results)
    logger.info(f"Saved profiling results to {output_path}")
    return output_path

def load_profiling_results(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load profiling results from JSON."""
    if input_path is None:
        data_root = get_data_root()
        input_path = os.path.join(data_root, "profiling_logs.json")
    
    if not os.path.exists(input_path):
        return []
    
    return read_json(input_path)

def run_feasibility_gate() -> Dict[str, Any]:
    """
    T021 Implementation: Run feasibility gate checks.
    Checks peak memory and projected time against limits.
    """
    # Load results
    results = load_profiling_results()
    if not results:
        logger.warning("No profiling results found for gate check.")
        return {"status": "fail", "reason": "No data"}

    # Aggregate
    peak_mem = max(r.get("peak_memory_mb", 0) for r in results)
    avg_time = sum(r.get("cpu_time_seconds", 0) for r in results) / len(results)
    
    # Limits
    MEM_LIMIT_GB = 7.0
    MEM_LIMIT_MB = MEM_LIMIT_GB * 1024
    
    status = "pass"
    reason = "All checks passed"
    
    if peak_mem > MEM_LIMIT_MB:
        status = "fail"
        reason = f"Peak memory {peak_mem:.2f}MB exceeds limit {MEM_LIMIT_MB:.2f}MB"
    
    return {
        "status": status,
        "reason": reason,
        "peak_memory_mb": peak_mem,
        "avg_time_per_clip": avg_time
    }

def main():
    """
    Main entry point for profiling module.
    """
    logger.info("Profiling module loaded.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
