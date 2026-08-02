"""
Pipeline Orchestrator for Statistical Analysis of VAERS Data.

This module enforces phase order, performs memory checks, and coordinates
the execution of data acquisition, cleaning, analysis, and reporting stages.
"""
import os
import sys
import gc
import logging
import argparse
from pathlib import Path
from typing import List, Optional

# Add project root to path to ensure imports work correctly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import ensure_dirs
from src.data.download import fetch_vaers_data, main as download_main
from src.data.validate import validate_data, main as validate_main
from src.data.clean import process_data, get_memory_usage_gb, main as clean_main
from src.analysis.disproportionality import run_analysis, main as analysis_main
from src.analysis.temporal import generate_temporal_profiles, main as temporal_main
from src.analysis.sensitivity import run_sensitivity_analysis, main as sensitivity_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Memory thresholds (in GB)
MEMORY_THRESHOLD_CLEANING = 5.0
MEMORY_THRESHOLD_ANALYSIS = 7.0

def check_memory_usage(threshold_gb: float, stage_name: str) -> bool:
    """
    Check current memory usage. If it exceeds the threshold, log a warning
    and attempt to free memory. If still high, raise an error.

    Returns True if safe to proceed, False if halted.
    """
    current_gb = get_memory_usage_gb()
    if current_gb > threshold_gb:
        logger.warning(f"Memory usage ({current_gb:.2f} GB) exceeds threshold ({threshold_gb} GB) for {stage_name}.")
        logger.info("Attempting garbage collection to free memory...")
        gc.collect()
        current_gb = get_memory_usage_gb()
        
        if current_gb > threshold_gb:
            logger.error(f"Memory usage ({current_gb:.2f} GB) still exceeds threshold ({threshold_gb} GB) after cleanup. Halting {stage_name}.")
            return False
        else:
            logger.info(f"Memory usage reduced to {current_gb:.2f} GB after cleanup. Proceeding.")
    return True

def run_phase_1_setup():
    """Initialize project directories."""
    logger.info("Starting Phase 1: Setup")
    ensure_dirs()
    logger.info("Phase 1: Setup completed.")

def run_phase_2_validation():
    """Validate raw data against schema."""
    logger.info("Starting Phase 2: Validation")
    # Ensure raw data exists first if not already done
    raw_data_dir = PROJECT_ROOT / 'data' / 'raw'
    if not any(raw_data_dir.glob('*.csv')):
        logger.warning("No raw data found. Running download phase first.")
        run_phase_data_acquisition()
    
    validate_main()
    logger.info("Phase 2: Validation completed.")

def run_phase_data_acquisition():
    """Download VAERS data."""
    logger.info("Starting Data Acquisition Phase")
    download_main()
    logger.info("Data Acquisition Phase completed.")

def run_phase_3_cleaning():
    """Clean and preprocess data with memory checks."""
    logger.info("Starting Phase 3: Data Cleaning")
    
    if not check_memory_usage(MEMORY_THRESHOLD_CLEANING, "Data Cleaning"):
        raise MemoryError("Data Cleaning halted due to memory constraints.")
    
    clean_main()
    
    logger.info("Phase 3: Data Cleaning completed.")

def run_phase_4_analysis():
    """Run disproportionality analysis with memory checks."""
    logger.info("Starting Phase 4: Disproportionality Analysis")
    
    if not check_memory_usage(MEMORY_THRESHOLD_ANALYSIS, "Disproportionality Analysis"):
        raise MemoryError("Disproportionality Analysis halted due to memory constraints.")
    
    analysis_main()
    logger.info("Phase 4: Disproportionality Analysis completed.")

def run_phase_5_temporal():
    """Generate temporal profiles."""
    logger.info("Starting Phase 5: Temporal Analysis")
    temporal_main()
    logger.info("Phase 5: Temporal Analysis completed.")

def run_phase_6_sensitivity():
    """Run sensitivity analysis."""
    logger.info("Starting Phase 6: Sensitivity Analysis")
    sensitivity_main()
    logger.info("Phase 6: Sensitivity Analysis completed.")

def run_full_pipeline():
    """Execute the full pipeline in order."""
    logger.info("Starting Full Pipeline Execution")
    
    try:
        run_phase_1_setup()
        run_phase_data_acquisition() # T013
        run_phase_2_validation()     # T007
        run_phase_3_cleaning()       # T014
        run_phase_4_analysis()       # T022-T028
        run_phase_5_temporal()       # T032-T035
        run_phase_6_sensitivity()    # T027
        
        logger.info("Full Pipeline Execution completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline Orchestrator")
    parser.add_argument(
        '--stage',
        choices=['setup', 'download', 'validate', 'clean', 'analyze', 'temporal', 'sensitivity', 'full'],
        default='full',
        help='Specific stage to run. Defaults to full pipeline.'
    )
    args = parser.parse_args()

    if args.stage == 'setup':
        run_phase_1_setup()
    elif args.stage == 'download':
        run_phase_data_acquisition()
    elif args.stage == 'validate':
        run_phase_2_validation()
    elif args.stage == 'clean':
        run_phase_3_cleaning()
    elif args.stage == 'analyze':
        run_phase_4_analysis()
    elif args.stage == 'temporal':
        run_phase_5_temporal()
    elif args.stage == 'sensitivity':
        run_phase_6_sensitivity()
    elif args.stage == 'full':
        run_full_pipeline()

    logger.info(f"Stage '{args.stage}' finished.")

if __name__ == '__main__':
    main()