"""
Memory monitoring utility for the perovskite stability pipeline.
Verifies that the full pipeline execution stays within the 7GB RAM constraint.
"""
import os
import sys
import time
import logging
import subprocess
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import psutil
except ImportError:
    print("ERROR: psutil is required for memory monitoring. Install with: pip install psutil")
    sys.exit(1)

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)
MAX_MEMORY_GB = 7.0
MEMORY_THRESHOLD_BYTES = MAX_MEMORY_GB * 1024**3

def get_current_memory_usage_gb() -> float:
    """Get the current memory usage of the current process in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024**3)

def run_script_with_memory_monitoring(script_path: str, args: Optional[list] = None) -> Dict[str, Any]:
    """
    Run a script while monitoring its peak memory usage.
    
    Args:
        script_path: Path to the Python script to run
        args: Optional list of command line arguments to pass to the script
        
    Returns:
        Dictionary with execution results and memory statistics
    """
    logger.info(f"Starting memory monitoring for script: {script_path}")
    logger.info(f"Memory limit set to: {MAX_MEMORY_GB} GB")
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    start_time = time.time()
    peak_memory_gb = 0.0
    success = False
    error_message = None
    
    try:
        # Start the subprocess
        process = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        memory_samples = []
        
        # Monitor memory while the process runs
        while process.poll() is None:
            try:
                mem_gb = get_current_memory_usage_gb()
                memory_samples.append(mem_gb)
                if mem_gb > peak_memory_gb:
                    peak_memory_gb = mem_gb
                
                # Log progress if memory is approaching limit
                if mem_gb > (MAX_MEMORY_GB * 0.8):
                    logger.warning(f"Memory usage approaching limit: {mem_gb:.2f} GB")
                
                time.sleep(0.5)  # Sample every 500ms
            except psutil.NoSuchProcess:
                break
            except Exception as e:
                logger.warning(f"Error monitoring memory: {e}")
                break
        
        # Final memory check
        try:
            final_mem_gb = get_current_memory_usage_gb()
            memory_samples.append(final_mem_gb)
            if final_mem_gb > peak_memory_gb:
                peak_memory_gb = final_mem_gb
        except Exception:
            pass
        
        # Wait for process to complete and capture output
        stdout, stderr = process.communicate()
        elapsed_time = time.time() - start_time
        
        if process.returncode == 0:
            success = True
            logger.info(f"Script completed successfully in {elapsed_time:.2f} seconds")
        else:
            error_message = f"Script failed with return code {process.returncode}"
            logger.error(f"{error_message}: {stderr.decode('utf-8', errors='ignore')}")
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_message = str(e)
        logger.error(f"Error running script: {e}")
    
    result = {
        "script": script_path,
        "success": success,
        "peak_memory_gb": peak_memory_gb,
        "memory_limit_gb": MAX_MEMORY_GB,
        "within_limit": peak_memory_gb <= MEMORY_THRESHOLD_BYTES,
        "elapsed_time_seconds": time.time() - start_time if 'elapsed_time' in locals() else 0,
        "error": error_message,
        "memory_samples": memory_samples[-10:] if memory_samples else []  # Last 10 samples
    }
    
    return result

def run_full_pipeline_memory_check() -> Dict[str, Any]:
    """
    Run the full pipeline with memory monitoring.
    Executes the main pipeline script and verifies memory usage stays under 7GB.
    """
    logger.info("=== Starting Full Pipeline Memory Verification ===")
    logger.info(f"Target: Verify peak RSS < {MAX_MEMORY_GB} GB")
    
    # Define the main pipeline script path
    pipeline_script = "code/pipeline.py"
    
    if not os.path.exists(pipeline_script):
        # Fallback to running individual stages if main pipeline doesn't exist
        logger.warning("Main pipeline script not found, attempting individual stage monitoring")
        stages = [
            "code/data/download.py",
            "code/data/descriptors.py",
            "code/data/preprocess.py",
            "code/models/train.py",
            "code/models/predict.py"
        ]
        
        results = []
        all_success = True
        max_peak_memory = 0.0
        
        for stage in stages:
            if os.path.exists(stage):
                logger.info(f"Monitoring stage: {stage}")
                result = run_script_with_memory_monitoring(stage)
                results.append(result)
                if result["peak_memory_gb"] > max_peak_memory:
                    max_peak_memory = result["peak_memory_gb"]
                if not result["success"]:
                    all_success = False
            else:
                logger.warning(f"Stage script not found: {stage}")
        
        return {
            "success": all_success,
            "peak_memory_gb": max_peak_memory,
            "within_limit": max_peak_memory <= MEMORY_THRESHOLD_BYTES,
            "stage_results": results,
            "error": None
        }
    
    # Run the main pipeline
    result = run_script_with_memory_monitoring(pipeline_script)
    return result

def main():
    """Main entry point for memory monitoring task."""
    parser = argparse.ArgumentParser(description="Monitor memory usage of the perovskite pipeline")
    parser.add_argument(
        "--script",
        type=str,
        default="code/pipeline.py",
        help="Path to the script to monitor (default: code/pipeline.py)"
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run the full pipeline memory check instead of a single script"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/memory_report.json",
        help="Path to save the memory report JSON"
    )
    
    args = parser.parse_args()
    
    log_pipeline_event("Memory monitoring started", {"mode": "full_pipeline" if args.full_pipeline else "single_script"})
    
    if args.full_pipeline:
        result = run_full_pipeline_memory_check()
    else:
        result = run_script_with_memory_monitoring(args.script)
    
    # Save report
    report_path = Path(args.output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Memory report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("MEMORY MONITORING SUMMARY")
    print("="*60)
    print(f"Script: {result['script']}")
    print(f"Success: {result['success']}")
    print(f"Peak Memory: {result['peak_memory_gb']:.2f} GB")
    print(f"Memory Limit: {result['memory_limit_gb']} GB")
    print(f"Within Limit: {result['within_limit']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    print("="*60)
    
    # Assert memory constraint
    if not result['within_limit']:
        print(f"\n⚠️  WARNING: Peak memory ({result['peak_memory_gb']:.2f} GB) exceeded limit ({result['memory_limit_gb']} GB)")
        sys.exit(1)
    else:
        print(f"\n✅ SUCCESS: Memory usage ({result['peak_memory_gb']:.2f} GB) is within the {result['memory_limit_gb']} GB limit")
        sys.exit(0)

if __name__ == "__main__":
    main()
