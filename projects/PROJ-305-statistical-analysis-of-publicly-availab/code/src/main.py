import os
import sys
import gc
import logging
import argparse
import tracemalloc
import time
from pathlib import Path
from typing import Optional

# Import existing utilities from the project
from src.utils.config import ensure_dirs
from src.data.download import fetch_vaers_data
from src.data.validate import validate_data, load_schema
from src.data.clean import process_data, setup_logging as clean_setup_logging
from src.analysis.disproportionality import run_analysis as run_disproportionality_analysis
from src.analysis.sensitivity import run_sensitivity_analysis
from src.analysis.sensitivity_output import generate_sensitivity_delta_csv
from src.analysis.signal_output import generate_signals_csv
from src.analysis.temporal import run_temporal_preparation

# Constants
E_MEMORY_LIMIT = 100  # Custom exit code for memory limit
MEMORY_LOG_PATH = "logs/memory.log"
DEFAULT_MEMORY_LIMIT_GB = 7.0
PHASE_4_ANALYSIS_LIMIT_GB = 7.0

def setup_logging():
    """Configure logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("main")

def get_memory_usage_gb():
    """Get current memory usage in GB using tracemalloc."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024 * 1024)

def check_memory_usage(limit_gb: float, stage_name: str, logger: logging.Logger) -> bool:
    """
    Check current memory usage against the limit.
    Returns True if within limits, False if exceeded.
    Logs the violation to logs/memory.log and exits if exceeded.
    """
    current_mem = get_memory_usage_gb()
    if current_mem > limit_gb:
        log_msg = f"MEMORY_LIMIT_EXCEEDED: {current_mem:.2f} GB > {limit_gb:.2f} GB at {stage_name}"
        logger.error(log_msg)
        
        # Append to specific memory log file
        memory_log_path = Path(MEMORY_LOG_PATH)
        memory_log_path.parent.mkdir(exist_ok=True)
        with open(memory_log_path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {log_msg}\n")
        
        # Clean up memory before exit
        gc.collect()
        sys.exit(E_MEMORY_LIMIT)
    
    logger.info(f"Memory check at {stage_name}: {current_mem:.2f} GB / {limit_gb:.2f} GB - OK")
    return True

def run_phase_1_setup(logger: logging.Logger):
    """Initialize project directories."""
    logger.info("Starting Phase 1: Setup")
    ensure_dirs()
    logger.info("Phase 1 Complete")

def run_phase_2_validation(logger: logging.Logger):
    """Validate configuration and environment."""
    logger.info("Starting Phase 2: Validation")
    # Placeholder for config validation if needed
    logger.info("Phase 2 Complete")

def run_phase_data_acquisition(logger: logging.Logger):
    """Download and validate raw data."""
    logger.info("Starting Phase 3: Data Acquisition")
    # Fetch data
    fetch_vaers_data()
    logger.info("Phase 3 Complete")

def run_phase_3_cleaning(logger: logging.Logger):
    """Clean and process data."""
    logger.info("Starting Phase 4: Cleaning")
    # Run cleaning process which includes its own memory checks
    process_data()
    logger.info("Phase 4 Complete")

def run_phase_4_analysis(logger: logging.Logger):
    """
    Perform disproportionality analysis.
    Includes specific memory check for Phase 4 (US2) with 7GB limit.
    """
    logger.info("Starting Phase 5: Disproportionality Analysis")
    
    # Start memory tracing if not already active
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    # Check memory BEFORE starting heavy analysis
    check_memory_usage(PHASE_4_ANALYSIS_LIMIT_GB, "Pre-Analysis", logger)
    
    # Run the main analysis
    run_disproportionality_analysis()
    
    # Check memory AFTER analysis before generating outputs
    check_memory_usage(PHASE_4_ANALYSIS_LIMIT_GB, "Post-Analysis", logger)
    
    # Generate signal output
    generate_signals_csv()
    
    # Run sensitivity analysis
    run_sensitivity_analysis()
    
    # Generate sensitivity output
    generate_sensitivity_delta_csv()
    
    # Final check
    check_memory_usage(PHASE_4_ANALYSIS_LIMIT_GB, "Post-Sensitivity", logger)
    
    logger.info("Phase 5 Complete")

def run_full_pipeline():
    """Execute the entire pipeline."""
    logger = setup_logging()
    ensure_dirs()
    
    # Start tracing memory for the whole run
    tracemalloc.start()
    
    try:
        run_phase_1_setup(logger)
        run_phase_2_validation(logger)
        run_phase_data_acquisition(logger)
        run_phase_3_cleaning(logger)
        run_phase_4_analysis(logger)
        run_temporal_preparation(logger)
        
        logger.info("Pipeline completed successfully.")
    except SystemExit as e:
        if e.code == E_MEMORY_LIMIT:
            logger.error("Pipeline halted due to memory limit.")
        raise

def main():
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline")
    parser.add_argument("--phase", choices=["all", "1", "2", "3", "4", "5"], default="all",
                        help="Specify which phase to run")
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if args.phase == "all":
        run_full_pipeline()
    elif args.phase == "1":
        run_phase_1_setup(logger)
    elif args.phase == "2":
        run_phase_2_validation(logger)
    elif args.phase == "3":
        run_phase_data_acquisition(logger)
    elif args.phase == "4":
        run_phase_3_cleaning(logger)
    elif args.phase == "5":
        run_phase_4_analysis(logger)

if __name__ == "__main__":
    main()