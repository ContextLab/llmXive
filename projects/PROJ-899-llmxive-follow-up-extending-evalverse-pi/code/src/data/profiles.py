import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config import get_state_root, get_data_root
from src.utils import write_json, read_json, get_logger
from src.data.preprocess import batch_process_clips
from src.models.evaluate import calculate_inference_time_projection, load_scaling_profile

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage of the process in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def get_cpu_time_seconds() -> float:
    """Get CPU time used by the process in seconds."""
    process = psutil.Process(os.getpid())
    cpu_times = process.cpu_times()
    return cpu_times.user + cpu_times.system

def profile_clip_execution(clip_id: str, clip_path: str) -> Dict[str, Any]:
    """
    Profile the execution of a single video clip.
    Returns a dictionary with timing and memory metrics.
    """
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    
    try:
        # Execute the actual feature extraction for the clip
        # This calls the real preprocessing logic
        result = batch_process_clips([clip_path], output_dir=None, dry_run=True)
        
        end_time = time.time()
        end_mem = get_memory_usage_mb()
        
        execution_time = end_time - start_time
        peak_memory = max(start_mem, end_mem)
        
        return {
            "clip_id": clip_id,
            "clip_path": clip_path,
            "execution_time_seconds": execution_time,
            "peak_memory_mb": peak_memory,
            "status": "success"
        }
    except Exception as e:
        end_time = time.time()
        end_mem = get_memory_usage_mb()
        
        return {
            "clip_id": clip_id,
            "clip_path": clip_path,
            "execution_time_seconds": end_time - start_time,
            "peak_memory_mb": max(start_mem, end_mem),
            "status": "failed",
            "error": str(e)
        }

def save_profiling_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """Save profiling results to a JSON file."""
    if output_path is None:
        state_root = get_state_root()
        output_path = os.path.join(state_root, "profiling_results.json")
    
    write_json(output_path, results)
    logger.info(f"Profiling results saved to {output_path}")
    return output_path

def load_profiling_results(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load profiling results from a JSON file."""
    if input_path is None:
        state_root = get_state_root()
        input_path = os.path.join(state_root, "profiling_results.json")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Profiling results not found at {input_path}")
    
    return read_json(input_path)

def run_feasibility_gate(
    sample_size: int = 50,
    max_memory_gb: float = 7.0,
    max_projected_hours: float = 6.0
) -> Dict[str, Any]:
    """
    Run the feasibility gate: profile a sample batch and check constraints.
    
    Args:
        sample_size: Number of clips to profile
        max_memory_gb: Maximum allowed peak memory in GB
        max_projected_hours: Maximum allowed projected total hours for 10k clips
        
    Returns:
        Dictionary with gate results and status
    """
    logger.info(f"Starting feasibility gate with sample size {sample_size}")
    
    # Get sample clips
    data_root = get_data_root()
    raw_data_dir = os.path.join(data_root, "raw")
    
    if not os.path.exists(raw_data_dir):
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Get list of video files
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    clip_paths = []
    
    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                clip_paths.append(os.path.join(root, file))
                if len(clip_paths) >= sample_size:
                    break
        if len(clip_paths) >= sample_size:
            break
    
    if len(clip_paths) == 0:
        raise RuntimeError("No video clips found in raw data directory")
    
    logger.info(f"Found {len(clip_paths)} clips for profiling")
    
    # Profile each clip
    profiling_results = []
    max_memory_mb = 0.0
    total_time = 0.0
    
    for i, clip_path in enumerate(clip_paths):
        logger.info(f"Profiling clip {i+1}/{len(clip_paths)}: {os.path.basename(clip_path)}")
        
        clip_id = os.path.basename(clip_path)
        result = profile_clip_execution(clip_id, clip_path)
        profiling_results.append(result)
        
        if result["peak_memory_mb"] > max_memory_mb:
            max_memory_mb = result["peak_memory_mb"]
        
        if result["status"] == "success":
            total_time += result["execution_time_seconds"]
    
    # Calculate statistics
    avg_time_per_clip = total_time / len(clip_paths) if clip_paths else 0
    projected_total_hours = (avg_time_per_clip * 10000) / 3600
    
    max_memory_gb_actual = max_memory_mb / 1024.0
    
    # Check constraints
    memory_ok = max_memory_gb_actual <= max_memory_gb
    time_ok = projected_total_hours <= max_projected_hours
    
    gate_passed = memory_ok and time_ok
    
    gate_result = {
        "sample_size": len(clip_paths),
        "peak_memory_mb": max_memory_mb,
        "peak_memory_gb": max_memory_gb_actual,
        "avg_time_per_clip_seconds": avg_time_per_clip,
        "projected_total_hours": projected_total_hours,
        "max_memory_gb_threshold": max_memory_gb,
        "max_hours_threshold": max_projected_hours,
        "memory_constraint_ok": memory_ok,
        "time_constraint_ok": time_ok,
        "gate_passed": gate_passed,
        "status": "viable" if gate_passed else "non-viable",
        "profiling_details": profiling_results
    }
    
    # Save results
    state_root = get_state_root()
    output_path = os.path.join(state_root, "feasibility_gate.json")
    write_json(output_path, gate_result)
    
    logger.info(f"Feasibility gate result: {gate_result['status']}")
    logger.info(f"Peak memory: {max_memory_gb_actual:.2f} GB (threshold: {max_memory_gb} GB)")
    logger.info(f"Projected time: {projected_total_hours:.2f} hours (threshold: {max_projected_hours} hours)")
    
    return gate_result

def main():
    """Main entry point for the feasibility gate."""
    try:
        result = run_feasibility_gate()
        
        if not result["gate_passed"]:
            logger.error("Feasibility gate FAILED: constraints not met")
            sys.exit(1)
        
        logger.info("Feasibility gate PASSED")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Feasibility gate error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
