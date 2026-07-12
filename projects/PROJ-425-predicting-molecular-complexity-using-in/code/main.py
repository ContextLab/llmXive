import os
import sys
import time
import json
import logging
from pathlib import Path
import tracemalloc

# Add code directory to path if running from project root
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import (
    PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, REPORTS_DIR,
    SAMPLE_SIZE, LOG_LEVEL, get_log_file_path
)
from download import load_and_sample_dataset, compute_file_checksum, main as download_main
from metrics import main as metrics_main
from analysis import main as analysis_main
from viz import main as viz_main
from logging_setup import setup_logging, log_data_loading_stats

def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, REPORTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def run_download_step(logger):
    """Execute the download and sampling step."""
    logger.info("Starting download and sampling step...")
    start_time = time.time()
    
    try:
        stats = load_and_sample_dataset()
        checksum = compute_file_checksum(str(DATA_RAW_DIR / "pubchemm_canonicalized_sample.parquet"))
        duration = time.time() - start_time
        
        log_data_loading_stats(
            total_loaded=stats.get("total_loaded", 0),
            total_sampled=stats.get("total_sampled", 0),
            checksum=checksum,
            duration_seconds=duration
        )
        return True
    except Exception as e:
        logger.error(f"Download step failed: {e}")
        return False

def run_metrics_step(logger):
    """Execute the metrics computation step with memory profiling."""
    logger.info("Starting metrics computation step...")
    start_time = time.time()
    
    # Start memory profiling
    tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    logger.info(f"Memory profiling started. Current: {current / 1024**2:.2f} MB, Peak: {peak / 1024**2:.2f} MB")
    
    try:
        # Call metrics_main
        success = metrics_main()
        
        # Log peak memory usage after completion
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration = time.time() - start_time
        logger.info(f"Metrics step completed in {duration:.2f}s")
        logger.info(f"Peak memory usage during metrics computation: {peak / 1024**2:.2f} MB")
        
        if not success:
            logger.error("Metrics step failed")
            return False
            
        return True
    except Exception as e:
        tracemalloc.stop()
        logger.error(f"Metrics step failed with exception: {e}")
        return False

def run_analysis_step(logger):
    """Execute the analysis step."""
    logger.info("Starting analysis step...")
    start_time = time.time()
    
    success = analysis_main()
    
    duration = time.time() - start_time
    if success:
        logger.info(f"Analysis step completed successfully in {duration:.2f}s")
    else:
        logger.error("Analysis step failed")
    return success

def run_viz_step(logger):
    """Execute the visualization step."""
    logger.info("Starting visualization step...")
    start_time = time.time()
    
    success = viz_main()
    
    duration = time.time() - start_time
    if success:
        logger.info(f"Visualization step completed successfully in {duration:.2f}s")
    else:
        logger.error("Visualization step failed")
    return success

def main():
    """Main orchestration entry point."""
    # Setup logging first
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("Starting llmXive Molecular Complexity Pipeline")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    ensure_directories()
    
    # 1. Download
    if not run_download_step(logger):
        logger.error("Pipeline aborted: Download step failed.")
        return 1
    
    # 2. Metrics
    if not run_metrics_step(logger):
        logger.error("Pipeline aborted: Metrics step failed.")
        return 1
    
    # 3. Analysis
    if not run_analysis_step(logger):
        logger.error("Pipeline aborted: Analysis step failed.")
        return 1
    
    # 4. Visualization
    if not run_viz_step(logger):
        logger.error("Pipeline aborted: Visualization step failed.")
        return 1
    
    total_duration = time.time() - start_time
    logger.info(f"Pipeline completed successfully in {total_duration:.2f}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())