"""
Memory Profiling Wrapper for the Cognitive Fatigue Pipeline.

This script wraps the full pipeline execution to measure peak memory usage
of the entire process (including OS overhead) as required by T045 and T048.
It runs the pipeline stages sequentially and logs the peak memory to
data/analysis/memory_report.json.

It relies on the `memory_profiler` package being installed (added in T004).
"""

import os
import sys
import time
import json
import traceback
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import pipeline stages
from download import main as run_download
from preprocess import main as run_preprocess
from features import main as run_features
from analysis import main as run_analysis
from report import main as run_report

# Import memory profiling utility
from verify_memory import get_peak_memory_mb

LOG_FILE = "logs/memory_profile.log"
REPORT_FILE = "data/analysis/memory_report.json"

def setup_logger():
    """Initialize logging for the memory profiling run."""
    import logging
    from utils.logging import get_logger
    logger = get_logger("memory_profile")
    logger.setLevel(logging.INFO)
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing file handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

def run_stage_with_memory(stage_name, stage_func, logger):
    """
    Run a specific pipeline stage and log memory usage.
    
    Args:
        stage_name (str): Name of the stage for logging.
        stage_func (callable): The function to execute (must be the stage's main).
        logger (logging.Logger): Logger instance.
        
    Returns:
        bool: True if stage succeeded, False otherwise.
    """
    logger.info(f"Starting stage: {stage_name}")
    start_time = time.time()
    
    try:
        # Reset peak memory tracking before stage
        # Note: get_peak_memory_mb() returns current + historical peak for the process
        # We rely on the global resource module tracking for the whole process.
        
        stage_func()
        
        duration = time.time() - start_time
        current_mem = get_peak_memory_mb()
        logger.info(f"Stage {stage_name} completed successfully in {duration:.2f}s. Peak memory: {current_mem:.2f} MB")
        return True
        
    except SystemExit as e:
        duration = time.time() - start_time
        logger.error(f"Stage {stage_name} exited with code {e.code} after {duration:.2f}s")
        return False
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Stage {stage_name} failed with exception: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Execute the full pipeline with memory profiling.
    
    This function orchestrates the execution of all pipeline stages:
    Download -> Preprocess -> Features -> Analysis -> Report.
    It tracks the peak memory usage of the entire process and writes
    the results to data/analysis/memory_report.json.
    """
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("Starting Memory Profiling Run for Cognitive Fatigue Pipeline")
    logger.info("=" * 60)
    
    pipeline_stages = [
        ("Download", run_download),
        ("Preprocess", run_preprocess),
        ("Features", run_features),
        ("Analysis", run_analysis),
        ("Report", run_report),
    ]
    
    success_count = 0
    failed_stages = []
    
    for name, func in pipeline_stages:
        if not run_stage_with_memory(name, func, logger):
            failed_stages.append(name)
            logger.warning(f"Pipeline halted due to failure in stage: {name}")
            break
        success_count += 1
    
    # Capture final peak memory
    final_peak_mem = get_peak_memory_mb()
    
    # Prepare report
    report = {
        "pipeline_name": "Cognitive Fatigue Prediction",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_stages": len(pipeline_stages),
        "successful_stages": success_count,
        "failed_stages": failed_stages,
        "peak_memory_mb": final_peak_mem,
        "limit_mb": 7000.0,  # 7 GB limit as per SC-003
        "status": "PASS" if final_peak_mem < 7000.0 else "FAIL",
        "stages_completed": [name for name, _ in pipeline_stages[:success_count]]
    }
    
    # Ensure output directory exists
    report_path = Path(REPORT_FILE)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Memory report written to {REPORT_FILE}")
    logger.info(f"Final Peak Memory: {final_peak_mem:.2f} MB")
    logger.info(f"Status: {report['status']}")
    logger.info("=" * 60)
    
    # Return exit code based on status
    if failed_stages:
        logger.error(f"Pipeline failed at stage(s): {', '.join(failed_stages)}")
        sys.exit(1)
    elif report['status'] == "FAIL":
        logger.warning(f"Memory limit exceeded: {final_peak_mem:.2f} MB > 7000 MB")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully within memory limits.")
        sys.exit(0)

if __name__ == "__main__":
    main()