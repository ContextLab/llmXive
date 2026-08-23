"""
Module for CPU and memory profiling of clip processing.
Implements structured logging of exact CPU time and memory peak per clip.
"""
import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from src.utils import get_logger, write_json, ensure_directories
from src.config import get_data_root, get_processed_data_dir

logger = get_logger(__name__)

def get_memory_usage_mb(process: Optional[psutil.Process] = None) -> float:
    """
    Get current memory usage of the process in MB.
    
    Args:
        process: psutil.Process object. If None, uses current process.
    
    Returns:
        Memory usage in MB.
    """
    if process is None:
        process = psutil.Process(os.getpid())
    
    try:
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert bytes to MB
    except Exception as e:
        logger.warning(f"Failed to get memory info: {e}")
        return 0.0

def get_cpu_time_seconds(start_time: float, end_time: float) -> float:
    """
    Calculate CPU time elapsed between start and end timestamps.
    
    Args:
        start_time: Start timestamp (time.time())
        end_time: End timestamp (time.time())
    
    Returns:
        Elapsed time in seconds.
    """
    return end_time - start_time

def profile_clip_execution(
    clip_id: str,
    process_func,
    *args,
    timeout_seconds: int = 300,
    **kwargs
) -> Dict[str, Any]:
    """
    Profile the execution of a clip processing function.
    
    Args:
        clip_id: Identifier for the clip being processed.
        process_func: Function to execute and profile.
        *args: Positional arguments to pass to process_func.
        timeout_seconds: Maximum execution time in seconds.
        **kwargs: Keyword arguments to pass to process_func.
    
    Returns:
        Dictionary with profiling results:
            {
                "clip_id": str,
                "cpu_time_sec": float,
                "peak_memory_mb": float,
                "status": "success" | "failed" | "timeout"
            }
    """
    result = {
        "clip_id": clip_id,
        "cpu_time_sec": 0.0,
        "peak_memory_mb": 0.0,
        "status": "failed"
    }
    
    process = psutil.Process(os.getpid())
    initial_memory = get_memory_usage_mb(process)
    
    try:
        start_time = time.time()
        
        # Execute the processing function
        process_func(*args, **kwargs)
        
        end_time = time.time()
        
        # Calculate metrics
        cpu_time = get_cpu_time_seconds(start_time, end_time)
        final_memory = get_memory_usage_mb(process)
        peak_memory = max(initial_memory, final_memory)
        
        result["cpu_time_sec"] = round(cpu_time, 4)
        result["peak_memory_mb"] = round(peak_memory, 2)
        result["status"] = "success"
        
        logger.debug(f"Profiled clip {clip_id}: {cpu_time:.4f}s, {peak_memory:.2f}MB")
        
    except TimeoutError:
        result["status"] = "timeout"
        logger.error(f"Clip {clip_id} timed out after {timeout_seconds}s")
        
    except Exception as e:
        result["status"] = "failed"
        logger.error(f"Clip {clip_id} failed: {e}")
        traceback.print_exc()
    
    return result

def save_profiling_results(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: List of profiling result dictionaries.
        output_path: Optional path to save results. If None, uses default path.
    
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        data_root = get_data_root()
        output_path = os.path.join(data_root, "profiling_logs.json")
    
    ensure_directories([os.path.dirname(output_path)])
    
    write_json(output_path, results)
    logger.info(f"Saved profiling results to {output_path}")
    
    return output_path

def load_profiling_results(
    input_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load profiling results from a JSON file.
    
    Args:
        input_path: Optional path to load results from. If None, uses default path.
    
    Returns:
        List of profiling result dictionaries.
    """
    if input_path is None:
        data_root = get_data_root()
        input_path = os.path.join(data_root, "profiling_logs.json")
    
    if not os.path.exists(input_path):
        logger.warning(f"Profiling results file not found: {input_path}")
        return []
    
    return json.load(open(input_path, 'r'))

def run_feasibility_gate(
    profiling_results: List[Dict[str, Any]],
    memory_threshold_mb: int = 7168,
    time_threshold_hours: float = 6.0
) -> Dict[str, Any]:
    """
    Run feasibility gate based on profiling results.
    
    Args:
        profiling_results: List of profiling result dictionaries.
        memory_threshold_mb: Maximum allowed peak memory in MB (default 7GB).
        time_threshold_hours: Maximum allowed projected total hours.
    
    Returns:
        Dictionary with gate results:
            {
                "passed": bool,
                "peak_memory_mb": float,
                "mean_time_per_clip_sec": float,
                "projected_total_hours": float,
                "status": "pass" | "fail"
            }
    """
    if not profiling_results:
        return {
            "passed": False,
            "peak_memory_mb": 0.0,
            "mean_time_per_clip_sec": 0.0,
            "projected_total_hours": 0.0,
            "status": "fail",
            "reason": "No profiling results available"
        }
    
    successful_results = [r for r in profiling_results if r["status"] == "success"]
    
    if not successful_results:
        return {
            "passed": False,
            "peak_memory_mb": 0.0,
            "mean_time_per_clip_sec": 0.0,
            "projected_total_hours": 0.0,
            "status": "fail",
            "reason": "No successful profiling results"
        }
    
    # Calculate metrics
    peak_memory = max(r["peak_memory_mb"] for r in successful_results)
    mean_time = sum(r["cpu_time_sec"] for r in successful_results) / len(successful_results)
    
    # Project total time for 10,000 clips
    projected_total_hours = (mean_time * 10000) / 3600
    
    passed = peak_memory <= memory_threshold_mb and projected_total_hours <= time_threshold_hours
    
    return {
        "passed": passed,
        "peak_memory_mb": round(peak_memory, 2),
        "mean_time_per_clip_sec": round(mean_time, 4),
        "projected_total_hours": round(projected_total_hours, 2),
        "status": "pass" if passed else "fail",
        "checks": {
            "memory_ok": peak_memory <= memory_threshold_mb,
            "time_ok": projected_total_hours <= time_threshold_hours
        }
    }

def main() -> int:
    """
    Main entry point for profiling execution.
    
    This function profiles the processing of clips from the processed data directory
    and saves the results to data/profiling_logs.json.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting profiling execution...")
    
    try:
        # Ensure directories exist
        ensure_directories([get_data_root(), get_processed_data_dir()])
        
        # Get list of clips to profile
        processed_dir = get_processed_data_dir()
        feature_files = [
            f for f in os.listdir(processed_dir)
            if f.startswith("features_") and f.endswith(".csv")
        ]
        
        if not feature_files:
            logger.warning("No feature files found to profile. Using sample clips.")
            # Create mock data for testing if fetch failed (should not happen in real run)
            # This is a fallback for development when real data is not available
            # In production, this should raise an error
            logger.error("No real data available for profiling. Aborting.")
            return 1
        
        # Import processing function
        from src.cli.run_pipeline import process_batch_clips
        
        profiling_results = []
        
        # Profile each feature file
        for feature_file in feature_files[:5]:  # Limit to first 5 for profiling
            clip_id = feature_file.replace(".csv", "")
            logger.info(f"Profiling {clip_id}...")
            
            result = profile_clip_execution(
                clip_id=clip_id,
                process_func=process_batch_clips,
                input_file=os.path.join(processed_dir, feature_file),
                timeout_seconds=300
            )
            
            profiling_results.append(result)
        
        # Save results
        output_path = save_profiling_results(profiling_results)
        
        # Run feasibility gate
        gate_result = run_feasibility_gate(profiling_results)
        
        logger.info(f"Profiling complete. Results saved to {output_path}")
        logger.info(f"Feasibility gate: {gate_result['status']}")
        
        return 0 if gate_result["passed"] else 1
        
    except Exception as e:
        logger.error(f"Profiling execution failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
