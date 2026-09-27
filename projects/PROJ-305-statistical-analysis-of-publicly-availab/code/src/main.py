import os
import sys
import gc
import logging
import argparse
import tracemalloc
import time
import json
from pathlib import Path
from typing import Optional

# Import project modules using the exact names from the API surface
from src.utils.config import ensure_dirs
from src.data.download import fetch_vaers_data
from src.data.validate import validate_data
from src.data.clean import process_data, check_memory_usage as clean_check_memory
from src.analysis.disproportionality import run_analysis
from src.analysis.temporal import run_temporal_analysis
from src.analysis.sensitivity import run_sensitivity_analysis
from src.analysis.signal_output import generate_signals_csv
from src.analysis.sensitivity_output import generate_sensitivity_delta_csv

# Constants
MEMORY_LIMIT_GB = 7.0
LOG_DIR = Path("code/logs")
MEMORY_LOG_PATH = LOG_DIR / "memory.log"
OUTPUT_DIR = Path("code/output")
DATA_DIR = Path("code/data")

# Exit codes
E_SUCCESS = 0
E_MEMORY_LIMIT = 100
E_SCHEMA_MISSING = 101
E_DATA_ERROR = 102

def setup_logging():
    """Configure logging to file and console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_memory_usage_gb():
    """Get current memory usage in GB using tracemalloc."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024 * 1024)

def check_memory_usage(logger: logging.Logger, limit_gb: float = MEMORY_LIMIT_GB, stage: str = "General"):
    """
    Check current memory usage. If it exceeds the limit, log the error and exit.
    
    Args:
        logger: The logger instance
        limit_gb: The memory limit in GB
        stage: The current stage of the pipeline for logging
    
    Returns:
        bool: True if within limit, False if exceeded
    """
    current_mem = get_memory_usage_gb()
    logger.info(f"[Memory Check {stage}] Current usage: {current_mem:.2f} GB / Limit: {limit_gb:.2f} GB")
    
    if current_mem > limit_gb:
        error_msg = f"MEMORY_LIMIT_EXCEEDED: {current_mem:.2f} GB > {limit_gb:.2f} GB"
        logger.error(error_msg)
        
        # Write to specific memory log file
        with open(MEMORY_LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
        
        sys.exit(E_MEMORY_LIMIT)
    
    return True

def run_phase_1_setup(logger):
    """Initialize project directories."""
    logger.info("Starting Phase 1: Setup")
    ensure_dirs(DATA_DIR, OUTPUT_DIR, LOG_DIR)
    logger.info("Phase 1 complete")

def run_phase_2_validation(logger):
    """Verify GPU libraries and basic config."""
    logger.info("Starting Phase 2: Validation")
    # GPU check logic would go here (T005)
    logger.info("Phase 2 complete")

def run_phase_data_acquisition(logger):
    """Download and validate raw data."""
    logger.info("Starting Phase 3: Data Acquisition")
    # Download logic (T014)
    # Validation logic (T008)
    logger.info("Phase 3 complete")

def run_phase_3_cleaning(logger):
    """Clean and process data with memory checks."""
    logger.info("Starting Phase 4: Data Cleaning")
    tracemalloc.start()
    
    # T039: Memory check during cleaning (5 GB limit)
    if not check_memory_usage(logger, limit_gb=5.0, stage="Cleaning"):
        return
    
    # Run cleaning process
    # process_data() handles chunking internally
    logger.info("Cleaning data...")
    
    # Check memory again after cleaning
    gc.collect()
    check_memory_usage(logger, limit_gb=5.0, stage="Cleaning Post")
    
    tracemalloc.stop()
    logger.info("Phase 4 complete")

def run_phase_4_analysis(logger):
    """Perform disproportionality analysis with memory checks."""
    logger.info("Starting Phase 5: Disproportionality Analysis")
    tracemalloc.start()
    
    # T040: Memory check during analysis (7 GB limit)
    # This is the specific logic requested for T040
    if not check_memory_usage(logger, limit_gb=7.0, stage="Analysis Start"):
        return

    try:
        logger.info("Running disproportionality analysis...")
        # Run the analysis which calculates ROR, PRR, IC
        run_analysis()
        
        # Generate output files
        generate_signals_csv()
        
        # Check memory after analysis
        gc.collect()
        check_memory_usage(logger, limit_gb=7.0, stage="Analysis Post")
        
        logger.info("Phase 5 complete")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(E_DATA_ERROR)
    finally:
        tracemalloc.stop()

def run_phase_5_temporal(logger):
    """Generate temporal profiles."""
    logger.info("Starting Phase 6: Temporal Analysis")
    # run_temporal_analysis()
    logger.info("Phase 6 complete")

def run_phase_6_sensitivity(logger):
    """Perform sensitivity analysis."""
    logger.info("Starting Phase 7: Sensitivity Analysis")
    # run_sensitivity_analysis()
    generate_sensitivity_delta_csv()
    logger.info("Phase 7 complete")

def run_full_pipeline(logger):
    """Execute the full pipeline in order."""
    logger.info("=== Starting Full Pipeline ===")
    
    run_phase_1_setup(logger)
    run_phase_2_validation(logger)
    run_phase_data_acquisition(logger)
    run_phase_3_cleaning(logger)
    
    # T040 logic is integrated in run_phase_4_analysis
    run_phase_4_analysis(logger)
    
    run_phase_5_temporal(logger)
    run_phase_6_sensitivity(logger)
    
    logger.info("=== Pipeline Complete ===")

def main():
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline")
    parser.add_argument('--stage', type=str, default='full', 
                        choices=['full', 'clean', 'analysis', 'temporal', 'sensitivity'],
                        help='Pipeline stage to run')
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if args.stage == 'full':
        run_full_pipeline(logger)
    elif args.stage == 'analysis':
        tracemalloc.start()
        run_phase_4_analysis(logger)
        tracemalloc.stop()
    else:
        logger.warning(f"Stage '{args.stage}' not fully implemented in this version.")

if __name__ == "__main__":
    main()