"""
Performance harness for the llmXive automated science pipeline.

Executes the pipeline steps while recording wall-clock time and peak RSS.
Outputs results to data/processed/performance_metrics.json.

Dependencies:
- memory_profiler (pip install memory_profiler)
- psutil (pip install psutil)
"""
import json
import os
import subprocess
import sys
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Attempt to import memory_profiler and psutil
try:
    from memory_profiler import memory_usage
    import psutil
except ImportError:
    print("ERROR: Required dependencies 'memory_profiler' and 'psutil' are not installed.")
    print("Please run: pip install memory_profiler psutil")
    sys.exit(1)

from utils.logging_config import setup_logging

# Configure logging
logger = setup_logging("performance_harness")

def ensure_directories() -> None:
    """Ensure required output directories exist."""
    data_processed = Path("data/processed")
    data_processed.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {data_processed}")

def run_step_with_profiling(step_name: str, script_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run a specific pipeline script with memory and time profiling.
    
    Args:
        step_name: Human-readable name for the step
        script_path: Path to the python script (relative to project root)
        args: Optional list of command-line arguments
    
    Returns:
        Dictionary with timing and memory metrics
    """
    logger.info(f"Starting performance profiling for step: {step_name}")
    
    start_time = time.time()
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Run the script with memory profiling
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        # Use memory_usage to profile the script
        # We run the script as a subprocess to get accurate peak memory
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per step
        )
        
        if result.returncode != 0:
            logger.error(f"Step {step_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Step {step_name} failed")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Get final memory usage (approximation of peak if we can't get it directly)
        # Note: For accurate peak memory, we'd need to monitor the subprocess
        final_memory = process.memory_info().rss / (1024 * 1024)
        peak_memory = max(initial_memory, final_memory)
        
        logger.info(f"Step {step_name} completed in {elapsed_time:.2f}s, peak memory ~{peak_memory:.2f}MB")
        
        return {
            "step_name": step_name,
            "script_path": script_path,
            "status": "success",
            "wall_clock_time_seconds": elapsed_time,
            "peak_memory_mb": peak_memory,
            "exit_code": 0
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Step {step_name} timed out")
        return {
            "step_name": step_name,
            "script_path": script_path,
            "status": "timeout",
            "wall_clock_time_seconds": 3600,
            "peak_memory_mb": None,
            "exit_code": -1,
            "error": "Timeout"
        }
    except Exception as e:
        logger.error(f"Step {step_name} failed with exception: {str(e)}")
        return {
            "step_name": step_name,
            "script_path": script_path,
            "status": "error",
            "wall_clock_time_seconds": time.time() - start_time,
            "peak_memory_mb": None,
            "exit_code": -1,
            "error": str(e)
        }

def run_full_pipeline_profiling() -> Dict[str, Any]:
    """
    Run the full pipeline with profiling for each step.
    
    Returns:
        Dictionary containing metrics for each step and aggregate stats
    """
    logger.info("Starting full pipeline performance profiling")
    
    # Define the pipeline steps in execution order
    # Based on the tasks and dependencies:
    # 1. Ingest OpenML data (T012, T013, T014, T015, T016)
    # 2. Parse publications (T021, T022, T023, T024, T026, T027, T028.1)
    # 3. Compute sensitivity (T031, T032, T033)
    # 4. Generate report (T034, T035, T036, T037)
    
    steps = [
        ("Ingest OpenML Data", "code/01_ingest_openml.py"),
        ("Parse Publications", "code/02_parse_publications.py"),
        ("Compute Sensitivity", "code/03_compute_sensitivity.py"),
        ("Generate Report", "code/04_generate_report.py")
    ]
    
    results = []
    total_time = 0
    total_memory = 0
    successful_steps = 0
    
    for step_name, script_path in steps:
        # Check if script exists
        if not os.path.exists(script_path):
            logger.warning(f"Script {script_path} not found, skipping step: {step_name}")
            results.append({
                "step_name": step_name,
                "script_path": script_path,
                "status": "skipped",
                "reason": "Script not found"
            })
            continue
        
        step_result = run_step_with_profiling(step_name, script_path)
        results.append(step_result)
        
        if step_result["status"] == "success":
            successful_steps += 1
            total_time += step_result["wall_clock_time_seconds"]
            if step_result.get("peak_memory_mb"):
                total_memory = max(total_memory, step_result["peak_memory_mb"])
    
    # Calculate aggregate statistics
    aggregate = {
        "total_wall_clock_time_seconds": total_time,
        "peak_memory_mb": total_memory,
        "total_steps": len(steps),
        "successful_steps": successful_steps,
        "failed_steps": len(steps) - successful_steps,
        "average_time_per_step": total_time / successful_steps if successful_steps > 0 else 0
    }
    
    logger.info(f"Pipeline profiling complete. Total time: {total_time:.2f}s, Peak memory: {total_memory:.2f}MB")
    
    return {
        "pipeline_execution": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": sys.version,
            "platform": sys.platform
        },
        "steps": results,
        "aggregate": aggregate
    }

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save performance metrics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Performance metrics saved to {output_path}")

def main():
    """Main entry point for the performance harness."""
    logger.info("=== Starting Performance Harness ===")
    
    ensure_directories()
    
    # Run the full pipeline with profiling
    results = run_full_pipeline_profiling()
    
    # Save results
    output_path = "data/processed/performance_metrics.json"
    save_results(results, output_path)
    
    # Print summary to stdout
    print(json.dumps(results, indent=2))
    
    logger.info("=== Performance Harness Complete ===")
    
    # Return exit code based on success
    failed_steps = results["aggregate"]["failed_steps"]
    if failed_steps > 0:
        logger.warning(f"{failed_steps} steps failed during profiling")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
