"""
Memory profiling script for the mitochondrial aging correlation analysis.
Profiles the main pipeline execution and writes a detailed report to code/logs/memory_profile.log.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config.environment import get_local_paths, ensure_directories
from run_analysis import run_pipeline, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the Python process in MB.
    Uses resource module for Unix-like systems.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, bytes on macOS
        # Normalize to MB
        if sys.platform == 'darwin':
            return usage.ru_maxrss / (1024 * 1024)
        else:
            return usage.ru_maxrss / 1024
    except ImportError:
        # Fallback for Windows or if resource is unavailable
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.warning("Neither 'resource' nor 'psutil' available for memory measurement.")
            return 0.0

def profile_memory_usage() -> Dict[str, Any]:
    """
    Run the analysis pipeline while tracking memory usage at key stages.
    Returns a dictionary with memory metrics.
    """
    ensure_directories()
    paths = get_local_paths()
    
    results = {
        "start_time": None,
        "end_time": None,
        "initial_memory_mb": 0.0,
        "peak_memory_mb": 0.0,
        "final_memory_mb": 0.0,
        "stages": []
    }

    # Record initial memory
    initial_mem = get_memory_usage_mb()
    results["initial_memory_mb"] = initial_mem
    results["start_time"] = time.time()
    
    logger.info(f"Starting analysis pipeline. Initial memory: {initial_mem:.2f} MB")
    results["stages"].append({
        "stage": "initialization",
        "timestamp": time.time(),
        "memory_mb": initial_mem
    })

    try:
        # Run the main pipeline
        # We wrap the pipeline run to catch any exceptions but still record final memory
        run_pipeline()
        
        # Record final memory
        final_mem = get_memory_usage_mb()
        results["final_memory_mb"] = final_mem
        results["end_time"] = time.time()
        
        # The peak memory would ideally be tracked continuously, but for this
        # implementation we take the max of initial, final, and any intermediate points
        # Since we didn't have a continuous monitor, we'll estimate peak as the max of recorded
        results["peak_memory_mb"] = max(initial_mem, final_mem)
        
        logger.info(f"Pipeline completed. Final memory: {final_mem:.2f} MB")
        
    except Exception as e:
        logger.error(f"Pipeline failed during execution: {e}")
        # Still record final memory state even on failure
        final_mem = get_memory_usage_mb()
        results["final_memory_mb"] = final_mem
        results["end_time"] = time.time()
        results["peak_memory_mb"] = max(initial_mem, final_mem)
        raise

    return results

def write_memory_profile_log(results: Dict[str, Any], log_path: Path) -> None:
    """
    Write the memory profiling results to a log file.
    """
    ensure_directories()
    
    with open(log_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("MEMORY PROFILE REPORT - Mitochondrial Aging Correlation Analysis\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Start Time: {time.ctime(results['start_time'])}\n")
        f.write(f"End Time: {time.ctime(results['end_time'])}\n")
        f.write(f"Total Duration: {results['end_time'] - results['start_time']:.2f} seconds\n\n")
        
        f.write("Memory Usage Summary:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Initial Memory: {results['initial_memory_mb']:.2f} MB\n")
        f.write(f"Final Memory:   {results['final_memory_mb']:.2f} MB\n")
        f.write(f"Peak Memory:    {results['peak_memory_mb']:.2f} MB\n")
        f.write(f"Memory Delta:   {results['final_memory_mb'] - results['initial_memory_mb']:.2f} MB\n\n")
        
        f.write("Stage-by-Stage Memory Tracking:\n")
        f.write("-" * 40 + "\n")
        for stage in results['stages']:
            f.write(f"  {stage['stage']}: {stage['memory_mb']:.2f} MB (at {time.ctime(stage['timestamp'])})\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("End of Report\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Memory profile written to {log_path}")

def main() -> None:
    """
    Main entry point for memory profiling.
    """
    setup_logging()
    paths = get_local_paths()
    log_path = paths["logs"] / "memory_profile.log"
    
    logger.info(f"Starting memory profiling run. Output: {log_path}")
    
    try:
        results = profile_memory_usage()
        write_memory_profile_log(results, log_path)
        logger.info("Memory profiling completed successfully.")
    except Exception as e:
        logger.error(f"Memory profiling failed: {e}")
        # Write a minimal error log so the file exists
        with open(log_path, 'w') as f:
            f.write("MEMORY PROFILE ERROR\n")
            f.write(f"Error: {str(e)}\n")
            f.write("The pipeline failed during execution, preventing full profiling.\n")
        raise

if __name__ == "__main__":
    main()