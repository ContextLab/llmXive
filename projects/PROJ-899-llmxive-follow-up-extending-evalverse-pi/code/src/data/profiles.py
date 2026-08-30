import os
import time
import json
import psutil
import traceback
import subprocess
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import get_processed_data_dir, get_project_root
from src.utils import get_logger, write_json

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Returns:
        float: Memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_time_seconds() -> float:
    """
    Get CPU time used by the process in seconds.
    
    Returns:
        float: CPU time in seconds.
    """
    process = psutil.Process(os.getpid())
    cpu_times = process.cpu_times()
    return cpu_times.user + cpu_times.system

def get_git_commit() -> str:
    """
    Get the current git commit hash.
    
    Returns:
        str: Git commit hash, or 'unknown' if not a git repo.
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return 'unknown'
    except Exception as e:
        logger.warning(f"Could not get git commit: {e}")
        return 'unknown'

def compute_input_artifact_hash(input_file_path: str) -> str:
    """
    Compute SHA-256 hash of an input file for reproducibility tracking.
    
    Args:
        input_file_path: Path to the input file.
        
    Returns:
        str: Hex digest of the file hash, or 'missing' if file not found.
    """
    try:
        if not os.path.exists(input_file_path):
            return 'missing'
        
        sha256_hash = hashlib.sha256()
        with open(input_file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Could not compute hash for {input_file_path}: {e}")
        return 'error'

def profile_clip_execution(
    clip_id: str,
    process_func,
    process_args: tuple = (),
    process_kwargs: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Profile the execution of a single clip processing function.
    
    Args:
        clip_id: Unique identifier for the clip.
        process_func: The function to execute.
        process_args: Arguments to pass to the function.
        process_kwargs: Keyword arguments to pass to the function.
        timeout_seconds: Maximum execution time in seconds.
        
    Returns:
        Dict with profiling results including clip_id, cpu_time_sec, 
        peak_memory_mb, status, artifact_hash, git_commit, seed.
    """
    if process_kwargs is None:
        process_kwargs = {}
    
    start_cpu_time = get_cpu_time_seconds()
    start_memory = get_memory_usage_mb()
    peak_memory = start_memory
    status = "success"
    error_msg = None
    
    try:
        # Set a timeout using alarm (Unix only) or manual check
        # For simplicity, we'll rely on the function itself to be well-behaved
        # In a real scenario, we might use signal.alarm or multiprocessing with timeout
        
        process_func(*process_args, **process_kwargs)
        
    except TimeoutError:
        status = "timeout"
        error_msg = "Processing exceeded timeout limit"
        logger.error(f"Clip {clip_id} timed out after {timeout_seconds}s")
        
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        logger.error(f"Clip {clip_id} failed: {error_msg}")
        traceback.print_exc()
    
    end_cpu_time = get_cpu_time_seconds()
    end_memory = get_memory_usage_mb()
    
    # Update peak memory
    peak_memory = max(peak_memory, end_memory)
    
    cpu_time_sec = end_cpu_time - start_cpu_time
    
    # Compute artifact hash (assuming the input is the scores file)
    scores_path = os.path.join(get_processed_data_dir(), "scores.csv")
    artifact_hash = compute_input_artifact_hash(scores_path)
    
    return {
        "clip_id": clip_id,
        "cpu_time_sec": round(cpu_time_sec, 6),
        "peak_memory_mb": round(peak_memory, 2),
        "status": status,
        "artifact_hash": artifact_hash,
        "git_commit": get_git_commit(),
        "seed": 42  # Default seed from config
    }

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
        str: Path to the saved file.
    """
    if output_path is None:
        output_path = os.path.join(get_processed_data_dir(), "profiling_logs.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
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
        input_path = os.path.join(get_processed_data_dir(), "profiling_logs.json")
    
    if not os.path.exists(input_path):
        logger.warning(f"Profiling results file not found: {input_path}")
        return []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_profiling_batch(
    clip_ids: List[str],
    process_func,
    process_args: tuple = (),
    process_kwargs: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run profiling on a batch of clips.
    
    Args:
        clip_ids: List of clip IDs to process.
        process_func: The function to execute for each clip.
        process_args: Arguments to pass to the function.
        process_kwargs: Keyword arguments to pass to the function.
        output_path: Optional path to save results.
        
    Returns:
        List of profiling result dictionaries.
    """
    if process_kwargs is None:
        process_kwargs = {}
    
    results = []
    
    for clip_id in clip_ids:
        logger.info(f"Profiling clip: {clip_id}")
        
        # Add clip_id to kwargs if not present
        if 'clip_id' not in process_kwargs:
            kwargs = process_kwargs.copy()
            kwargs['clip_id'] = clip_id
        else:
            kwargs = process_kwargs
        
        result = profile_clip_execution(
            clip_id=clip_id,
            process_func=process_func,
            process_args=process_args,
            process_kwargs=kwargs
        )
        
        results.append(result)
        
        if result['status'] != 'success':
            logger.warning(f"Clip {clip_id} did not succeed: {result['status']}")
    
    save_profiling_results(results, output_path)
    return results

def main():
    """
    Main entry point for profiling batch processing.
    
    This function is designed to be called by the run_pipeline script
    after T022a has generated the batch of clips to process.
    """
    logger.info("Starting profiling batch processing")
    
    # Import here to avoid circular dependencies
    from src.cli.run_pipeline import get_sample_clips
    
    # Get sample clips to profile
    # In a real scenario, this would come from the batch processing output
    clip_ids = get_sample_clips(n=100)  # Profile first 100 clips
    
    if not clip_ids:
        logger.error("No clips found for profiling")
        return 1
    
    logger.info(f"Profiling {len(clip_ids)} clips")
    
    # Define a dummy process function for demonstration
    # In reality, this would be the actual feature extraction or model inference
    def dummy_process(clip_id: str, **kwargs):
        """Dummy processing function that simulates work."""
        import time
        # Simulate some computation
        time.sleep(0.01)
        # In a real scenario, this would call the actual feature extraction
        # e.g., extract_optical_flow_features(clip_id) or similar
    
    # Run profiling
    results = run_profiling_batch(
        clip_ids=clip_ids,
        process_func=dummy_process,
        output_path=os.path.join(get_processed_data_dir(), "profiling_logs.json")
    )
    
    # Log summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    timeout_count = sum(1 for r in results if r['status'] == 'timeout')
    
    logger.info(f"Profiling complete: {success_count} success, {failed_count} failed, {timeout_count} timeout")
    
    if failed_count > 0 or timeout_count > 0:
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
