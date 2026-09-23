"""
Timer utilities for wall-clock time monitoring and reporting.

Implements start_run, end_run, and log_split methods for tracking
execution time across pipeline stages (SC-005).
"""
import csv
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Global state for timing
_run_start_time: Optional[float] = None
_run_start_datetime: Optional[datetime] = None
_split_times: List[Dict[str, Any]] = []
_logger = logging.getLogger(__name__)

def start_run() -> None:
    """Start the wall-clock timer for the entire pipeline run."""
    global _run_start_time, _run_start_datetime, _split_times
    _run_start_time = time.time()
    _run_start_datetime = datetime.now()
    _split_times = []  # Reset split tracking
    _logger.info(f"Pipeline run started at {_run_start_datetime.isoformat()}")

def end_run() -> None:
    """Stop the wall-clock timer and log total duration."""
    global _run_start_time
    if _run_start_time is None:
        raise RuntimeError("start_run() must be called before end_run()")
    
    end_time = time.time()
    total_duration = end_time - _run_start_time
    _logger.info(f"Pipeline run ended. Total duration: {total_duration:.2f} seconds")
    _run_start_time = None

def log_split(split_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a timing split (intermediate checkpoint) with optional metadata.
    
    Args:
        split_name: Name of the pipeline stage (e.g., 'download', 'preprocess')
        metadata: Optional dictionary of additional context (e.g., paradigm_id, sample_size)
    """
    if _run_start_time is None:
        raise RuntimeError("start_run() must be called before log_split()")
    
    current_time = time.time()
    elapsed = current_time - _run_start_time
    
    split_record = {
        "split_name": split_name,
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "metadata": metadata or {}
    }
    _split_times.append(split_record)
    _logger.info(f"Split '{split_name}' logged at {elapsed:.2f}s")

def save_timing_report(output_path: str = "results/paper/timing_report.md") -> None:
    """
    Generate a markdown timing report with total duration and summary.
    
    Args:
        output_path: Path to the output markdown file
    """
    if _run_start_time is not None:
        raise RuntimeError("Cannot save report while run is still active. Call end_run() first.")
    
    if not _split_times:
        raise RuntimeError("No timing splits recorded. Cannot generate report.")
    
    total_duration = _split_times[-1]["elapsed_seconds"]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Pipeline Timing Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write(f"**Total Duration:** {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)\n\n")
        
        f.write("## Execution Budget\n")
        f.write(f"- **Budget Limit:** 300 seconds (5 minutes)\n")
        f.write(f"- **Actual Duration:** {total_duration:.2f} seconds\n")
        f.write(f"- **Status:** {'PASS' if total_duration <= 300 else 'FAIL'}\n\n")
        
        f.write("## Split Details\n")
        f.write("| Stage | Elapsed (s) | Metadata |\n")
        f.write("|-------|-------------|----------|\n")
        for split in _split_times:
            meta_str = ", ".join(f"{k}={v}" for k, v in split["metadata"].items()) if split["metadata"] else "-"
            f.write(f"| {split['split_name']} | {split['elapsed_seconds']:.2f} | {meta_str} |\n")
    
    _logger.info(f"Timing report saved to {output_path}")

def save_timing_breakdown(output_path: str = "results/paper/timing_breakdown.csv") -> None:
    """
    Save detailed timing breakdown to a CSV file.
    
    Args:
        output_path: Path to the output CSV file
    """
    if _run_start_time is not None:
        raise RuntimeError("Cannot save report while run is still active. Call end_run() first.")
    
    if not _split_times:
        raise RuntimeError("No timing splits recorded. Cannot generate CSV.")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["split_name", "timestamp", "elapsed_seconds", "metadata_json"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for split in _split_times:
            row = {
                "split_name": split["split_name"],
                "timestamp": split["timestamp"],
                "elapsed_seconds": split["elapsed_seconds"],
                "metadata_json": json.dumps(split["metadata"])
            }
            writer.writerow(row)
    
    _logger.info(f"Timing breakdown saved to {output_path}")

def run_pipeline_with_timing(pipeline_func, *args, **kwargs) -> Any:
    """
    Decorator-like wrapper to run a pipeline function with automatic timing.
    
    Args:
        pipeline_func: The pipeline function to execute
        *args: Positional arguments for the pipeline function
        **kwargs: Keyword arguments for the pipeline function
        
    Returns:
        The result of the pipeline function
    """
    start_run()
    try:
        result = pipeline_func(*args, **kwargs)
        end_run()
        return result
    except Exception as e:
        end_run()
        raise e

def main() -> None:
    """
    CLI entry point for testing the timer module.
    Simulates a pipeline run to generate the required output artifacts.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Simulate a pipeline run
    start_run()
    
    # Simulate stages with delays
    log_split("initialization", {"stage": "setup"})
    time.sleep(0.1)  # Simulate work
    
    log_split("data_download", {"dataset_id": "ds000030", "subjects": 10})
    time.sleep(0.2)
    
    log_split("preprocessing", {"kernel": "4mm", "roi_count": 90})
    time.sleep(0.15)
    
    log_split("glm_fitting", {"iterations": 100, "convergence": True})
    time.sleep(0.1)
    
    log_split("power_curve_generation", {"paradigms": 3, "alpha": 0.05})
    
    end_run()
    
    # Save outputs
    save_timing_report()
    save_timing_breakdown()
    
    print("Timing report generated successfully.")

if __name__ == "__main__":
    main()
