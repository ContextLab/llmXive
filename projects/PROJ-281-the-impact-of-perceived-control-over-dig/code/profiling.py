"""
Performance profiling script to verify runtime < 6h and RAM < 7GB.

This script wraps the main pipeline execution, measuring wall-clock time
and peak memory usage. It validates that the pipeline meets the constraints
specified in SC-004 (runtime < 6 hours) and system memory limits (< 7GB).

Output: data/processed/performance_report.json
"""
import argparse
import json
import logging
import resource
import time
from pathlib import Path
from typing import Dict, Any

import psutil

from code.config import CONFIG
from code.main import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(CONFIG.LOGS_DIR / "profiling.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024 ** 3

def get_memory_usage_gb() -> float:
    """Get current memory usage of the process in GB."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_peak_memory_gb() -> float:
    """Get peak memory usage of the process in GB (Unix only)."""
    # resource.getrusage returns peak RSS in kilobytes on Unix
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / (1024 * 1024)  # Convert KB to GB

def run_profiling_pipeline() -> Dict[str, Any]:
    """
    Run the full pipeline with performance monitoring.
    
    Returns:
        Dict containing performance metrics and pass/fail status.
    """
    logger.info("Starting performance profiling run...")
    
    start_time = time.time()
    initial_memory = get_memory_usage_gb()
    
    peak_memory = initial_memory
    try:
        # Run the main pipeline
        logger.info("Executing main pipeline...")
        run_pipeline()
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise
        
    end_time = time.time()
    final_memory = get_memory_usage_gb()
    
    # Calculate metrics
    runtime_seconds = end_time - start_time
    runtime_hours = runtime_seconds / 3600
    
    # On Unix, get peak from resource; otherwise use max observed
    try:
        peak_memory_gb = get_peak_memory_gb()
    except (AttributeError, OSError):
        # Fallback for Windows or if resource not available
        peak_memory_gb = max(initial_memory, final_memory)
    
    # Ensure we track peak from psutil as well for cross-platform consistency
    psutil_peak = get_memory_usage_gb()
    # Note: psutil memory_info().rss is current, not peak. 
    # We'll use the resource peak if available, else current max.
    # For strictness, we report the highest observed.
    
    results = {
        "pipeline_execution": {
            "status": "success",
            "start_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
            "end_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time)),
            "runtime_seconds": round(runtime_seconds, 2),
            "runtime_hours": round(runtime_hours, 4),
            "initial_memory_gb": round(initial_memory, 4),
            "final_memory_gb": round(final_memory, 4),
            "peak_memory_gb": round(peak_memory_gb, 4)
        },
        "constraints": {
            "max_runtime_hours": MAX_RUNTIME_SECONDS / 3600,
            "max_memory_gb": MAX_RAM_GB,
            "runtime_limit_seconds": MAX_RUNTIME_SECONDS,
            "memory_limit_bytes": MAX_RAM_BYTES
        },
        "validation": {
            "runtime_pass": runtime_seconds <= MAX_RUNTIME_SECONDS,
            "memory_pass": peak_memory_gb <= MAX_RAM_GB,
            "overall_pass": (runtime_seconds <= MAX_RUNTIME_SECONDS) and (peak_memory_gb <= MAX_RAM_GB)
        }
    }
    
    logger.info(f"Pipeline completed in {runtime_hours:.4f} hours.")
    logger.info(f"Peak memory usage: {peak_memory_gb:.4f} GB.")
    logger.info(f"Runtime constraint (<=6h): {'PASS' if results['validation']['runtime_pass'] else 'FAIL'}")
    logger.info(f"Memory constraint (<=7GB): {'PASS' if results['validation']['memory_pass'] else 'FAIL'}")
    
    return results

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the performance report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Performance report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run pipeline with performance profiling.")
    parser.add_argument(
        "--output",
        type=Path,
        default=CONFIG.PROCESSED_DIR / "performance_report.json",
        help="Path to save the performance report JSON."
    )
    args = parser.parse_args()

    try:
        report = run_profiling_pipeline()
        save_report(report, args.output)
        
        # Exit with error code if constraints failed
        if not report["validation"]["overall_pass"]:
            logger.error("Performance constraints NOT met. Exiting with error.")
            if not report["validation"]["runtime_pass"]:
                logger.error(f"Runtime exceeded limit: {report['pipeline_execution']['runtime_hours']:.2f}h > 6h")
            if not report["validation"]["memory_pass"]:
                logger.error(f"Memory exceeded limit: {report['pipeline_execution']['peak_memory_gb']:.2f}GB > 7GB")
            return 1
        
        logger.info("All performance constraints met successfully.")
        return 0
        
    except Exception as e:
        logger.exception(f"Profiling run failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
