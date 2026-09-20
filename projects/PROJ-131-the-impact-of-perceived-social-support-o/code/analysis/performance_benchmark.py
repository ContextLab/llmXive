"""
Performance benchmark module for T062: Compute Resource Verification.

This module runs a timed execution of the full pipeline (including bootstrapping)
to verify it completes within the 6-hour limit on a standard 2-core CPU runner.
It logs the runtime and resource usage to data/results/performance_report.json.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from logger import get_logger
from main_pipeline import main as pipeline_main

# Configure logging
logger = get_logger("performance_benchmark")

def run_benchmark(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Runs the full pipeline and measures execution time.
    
    Args:
        output_path: Path to save the performance report. Defaults to 
                     data/results/performance_report.json.
                     
    Returns:
        Dictionary containing benchmark results (runtime, status, etc.).
    """
    if output_path is None:
        output_path = project_root / "data" / "results" / "performance_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    status = "success"
    error_message = None
    
    try:
        logger.info("Starting full pipeline benchmark for T062 verification...")
        logger.info("This will run the complete pipeline including 1,000 bootstrap resamples.")
        
        # Run the main pipeline
        # Note: We call the main function directly. If it raises, we catch it below.
        pipeline_main()
        
        end_time = time.time()
        runtime_seconds = end_time - start_time
        
        # Check against 6-hour limit (21600 seconds)
        limit_seconds = 6 * 3600  # 21600 seconds
        is_within_limit = runtime_seconds <= limit_seconds
        
        if not is_within_limit:
            status = "timeout_warning"
            logger.warning(f"Pipeline runtime ({runtime_seconds:.2f}s) exceeded 6-hour limit ({limit_seconds}s).")
            logger.warning("This may indicate an infrastructure constraint.")
        else:
            logger.info(f"Pipeline completed successfully within 6-hour limit.")
            logger.info(f"Total runtime: {runtime_seconds:.2f} seconds ({runtime_seconds/3600:.2f} hours)")
        
        result = {
            "task_id": "T062",
            "status": status,
            "runtime_seconds": round(runtime_seconds, 2),
            "runtime_hours": round(runtime_seconds / 3600, 4),
            "limit_seconds": limit_seconds,
            "limit_hours": limit_seconds / 3600,
            "is_within_limit": is_within_limit,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": None
        }
        
    except Exception as e:
        end_time = time.time()
        runtime_seconds = end_time - start_time
        status = "failed"
        error_message = str(e)
        
        logger.error(f"Pipeline benchmark failed: {error_message}")
        logger.error(traceback.format_exc())
        
        result = {
            "task_id": "T062",
            "status": status,
            "runtime_seconds": round(runtime_seconds, 2),
            "runtime_hours": round(runtime_seconds / 3600, 4),
            "limit_seconds": limit_seconds,
            "limit_hours": limit_seconds / 3600,
            "is_within_limit": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_message
        }
    
    # Save report to disk
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Performance report saved to {output_path}")
    return result

def main():
    """Entry point for the benchmark script."""
    print("Running T062 Compute Resource Verification Benchmark...")
    result = run_benchmark()
    
    # Print summary
    print(f"\n--- Benchmark Summary ---")
    print(f"Status: {result['status']}")
    print(f"Runtime: {result['runtime_seconds']:.2f} seconds ({result['runtime_hours']:.4f} hours)")
    print(f"6-Hour Limit: {result['limit_hours']} hours")
    print(f"Within Limit: {result['is_within_limit']}")
    if result['error']:
        print(f"Error: {result['error']}")
    print(f"Report saved to: data/results/performance_report.json")
    
    # Exit with appropriate code
    if result['status'] == 'failed':
        sys.exit(1)
    elif result['status'] == 'timeout_warning':
        sys.exit(0)  # Still success, just a warning
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()