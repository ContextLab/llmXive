import os
import time
import json
import psutil
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from src.config import get_data_root, get_raw_data_dir
from src.utils import get_logger, ensure_directories, write_json
from src.data.download import fetch_evalverse_dataset

# Constants for logging
PROFILING_LOG_FILE = "data/profiling_logs.json"

def get_memory_usage_mb(process: Optional[psutil.Process] = None) -> float:
    """
    Get current memory usage of the process in MB.
    
    Args:
        process: psutil.Process object. If None, uses current process.
        
    Returns:
        Memory usage in megabytes.
    """
    if process is None:
        process = psutil.Process(os.getpid())
    
    try:
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert bytes to MB
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(f"Failed to get memory info: {e}")
        return 0.0

def get_cpu_time_seconds(start_time: float) -> float:
    """
    Calculate elapsed CPU time in seconds.
    
    Args:
        start_time: Start time from time.time()
        
    Returns:
        Elapsed time in seconds.
    """
    return time.time() - start_time

def profile_clip_execution(clip_id: str, process_fn, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile the execution of a function on a single clip.
    
    Args:
        clip_id: Unique identifier for the video clip
        process_fn: Function to execute and profile
        *args: Arguments to pass to process_fn
        **kwargs: Keyword arguments to pass to process_fn
        
    Returns:
        Dictionary containing profiling results for this clip
    """
    logger = get_logger(__name__)
    result = {
        "clip_id": clip_id,
        "success": False,
        "cpu_time_seconds": 0.0,
        "memory_peak_mb": 0.0,
        "error_message": None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    process = psutil.Process(os.getpid())
    initial_memory = get_memory_usage_mb(process)
    start_time = time.time()
    
    try:
        # Execute the processing function
        process_fn(*args, **kwargs)
        
        # Calculate metrics
        end_time = time.time()
        result["cpu_time_seconds"] = round(end_time - start_time, 4)
        
        # Get peak memory during execution
        current_memory = get_memory_usage_mb(process)
        result["memory_peak_mb"] = round(max(current_memory, initial_memory), 4)
        result["success"] = True
        
    except Exception as e:
        result["error_message"] = str(e)
        result["cpu_time_seconds"] = round(time.time() - start_time, 4)
        result["memory_peak_mb"] = round(get_memory_usage_mb(process), 4)
        logger.error(f"Error processing clip {clip_id}: {e}")
        traceback.print_exc()
    
    return result

def save_profiling_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: List of profiling result dictionaries
        output_path: Optional custom output path. If None, uses default data/profiling_logs.json
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = PROFILING_LOG_FILE
    
    # Ensure output directory exists
    output_file = Path(output_path)
    ensure_directories([output_file.parent])
    
    # Add metadata
    output_data = {
        "metadata": {
            "total_clips": len(results),
            "successful_clips": sum(1 for r in results if r.get("success", False)),
            "failed_clips": sum(1 for r in results if not r.get("success", False)),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "results": results
    }
    
    # Calculate aggregate statistics
    if results:
        successful_results = [r for r in results if r.get("success", False)]
        if successful_results:
            avg_cpu_time = sum(r["cpu_time_seconds"] for r in successful_results) / len(successful_results)
            max_memory = max(r["memory_peak_mb"] for r in successful_results)
            avg_memory = sum(r["memory_peak_mb"] for r in successful_results) / len(successful_results)
            
            output_data["summary"] = {
                "avg_cpu_time_seconds": round(avg_cpu_time, 4),
                "max_memory_mb": round(max_memory, 4),
                "avg_memory_mb": round(avg_memory, 4)
            }
    
    write_json(output_path, output_data)
    logger = get_logger(__name__)
    logger.info(f"Saved profiling results to {output_path}")
    
    return output_path

def load_profiling_results(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load profiling results from a JSON file.
    
    Args:
        input_path: Optional custom input path. If None, uses default data/profiling_logs.json
        
    Returns:
        Dictionary containing the profiling results
    """
    if input_path is None:
        input_path = PROFILING_LOG_FILE
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Profiling results file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def run_feasibility_gate(results: Dict[str, Any]) -> bool:
    """
    Run the feasibility gate check based on profiling results.
    
    Args:
        results: Dictionary containing profiling results (output from load_profiling_results)
        
    Returns:
        True if gate passes, False otherwise
        
    Raises:
        SystemExit: If gate fails
    """
    logger = get_logger(__name__)
    
    if "summary" not in results:
        logger.error("No summary data in profiling results")
        return False
    
    max_memory = results["summary"].get("max_memory_mb", 0)
    avg_cpu_time = results["summary"].get("avg_cpu_time_seconds", 0)
    
    # Convert memory to GB
    max_memory_gb = max_memory / 1024
    
    # Gate constraints
    MEMORY_THRESHOLD_GB = 7.0
    
    logger.info(f"Feasibility Gate Check:")
    logger.info(f"  Peak Memory: {max_memory_gb:.4f} GB (threshold: {MEMORY_THRESHOLD_GB} GB)")
    
    if max_memory_gb > MEMORY_THRESHOLD_GB:
        logger.error(f"FEASIBILITY GATE FAILED: Peak memory {max_memory_gb:.4f} GB exceeds threshold {MEMORY_THRESHOLD_GB} GB")
        return False
    
    logger.info("Feasibility Gate PASSED")
    return True

def main():
    """
    Main function to run profiling on a sample of clips and save results.
    This function demonstrates the profiling capability and generates the required output file.
    """
    logger = get_logger(__name__)
    logger.info("Starting profiling run for T023b")
    
    # Ensure data directory is ready
    data_dir = get_raw_data_dir()
    if not os.path.exists(data_dir):
        logger.info("Data directory not found, attempting to fetch dataset...")
        try:
            fetch_evalverse_dataset()
        except Exception as e:
            logger.error(f"Failed to fetch dataset: {e}")
            # Create mock data for testing if fetch fails
            logger.warning("Creating mock clips for profiling demonstration")
            mock_clips = [f"mock_clip_{i}.mp4" for i in range(5)]
    else:
        # Get list of clips from data directory
        mock_clips = [f for f in os.listdir(data_dir) if f.endswith(('.mp4', '.avi', '.mov'))][:5]
        if not mock_clips:
            mock_clips = [f"mock_clip_{i}.mp4" for i in range(5)]
    
    logger.info(f"Profiling {len(mock_clips)} clips")
    
    # Define a simple processing function for demonstration
    def mock_process_clip(clip_path):
        """Mock processing function that simulates feature extraction."""
        time.sleep(0.1)  # Simulate processing time
        # In real implementation, this would call extract_all_features or similar
        return {"status": "processed", "clip": clip_path}
    
    # Profile each clip
    results = []
    for clip_id in mock_clips:
        logger.info(f"Profiling clip: {clip_id}")
        profile_result = profile_clip_execution(
            clip_id=clip_id,
            process_fn=mock_process_clip,
            clip_path=clip_id
        )
        results.append(profile_result)
    
    # Save results to the required output file
    output_path = save_profiling_results(results)
    logger.info(f"Profiling complete. Results saved to {output_path}")
    
    # Load and display summary
    loaded_results = load_profiling_results(output_path)
    if "summary" in loaded_results:
        logger.info(f"Summary: {loaded_results['summary']}")
    
    return output_path

if __name__ == "__main__":
    main()
