import os
import sys
import gc
import logging
import argparse
import tracemalloc
import json
import time
from pathlib import Path
from typing import Optional

# Project-relative imports based on API surface
from src.utils.config import ensure_dirs
from src.data.download import fetch_vaers_data
from src.data.validate import validate_data
from src.data.clean import process_data, get_memory_usage_gb, check_memory_usage
from src.analysis.disproportionality import run_analysis
from src.analysis.signal_output import generate_signals_csv
from src.analysis.temporal import run_temporal_preparation
from src.analysis.sensitivity import run_sensitivity_analysis
from src.analysis.sensitivity_output import generate_sensitivity_delta_csv

# Constants
MEMORY_LIMIT_GB = 7.0
CLEANING_MEMORY_LIMIT_GB = 5.0
ANALYSIS_MEMORY_LIMIT_GB = 7.0
EXIT_CODE_MEMORY_LIMIT = 13  # Custom exit code for memory limit

# Setup logging
def setup_logging():
    """Configure logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("pipeline")

# Memory monitoring
def start_memory_profiling():
    """Start memory profiling."""
    tracemalloc.start()

def get_peak_memory_usage():
    """Get peak memory usage in GB."""
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def stop_memory_profiling():
    """Stop memory profiling and return stats."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
        return get_peak_memory_usage()
    return 0.0

def check_memory_usage(limit_gb: float, stage: str, logger: logging.Logger) -> bool:
    """Check current memory usage against limit."""
    current_mem = get_memory_usage_gb()
    if current_mem > limit_gb:
        logger.error(f"MEMORY_LIMIT_EXCEEDED: {current_mem:.2f} GB > {limit_gb:.2f} GB at {stage}")
        # Log to memory log file
        memory_log_path = Path("logs/memory.log")
        with open(memory_log_path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - MEMORY_LIMIT_EXCEEDED: {current_mem:.2f} GB > {limit_gb:.2f} GB at {stage}\n")
        return False
    logger.info(f"Memory usage at {stage}: {current_mem:.2f} GB (limit: {limit_gb:.2f} GB)")
    return True

# Phase execution functions
def run_phase_1_setup(logger: logging.Logger):
    """Run Phase 1: Project Setup."""
    logger.info("=== PHASE 1: PROJECT SETUP ===")
    ensure_dirs()
    logger.info("Phase 1 completed: Directories created")

def run_phase_2_validation(logger: logging.Logger):
    """Run Phase 2: Validation and GPU check."""
    logger.info("=== PHASE 2: VALIDATION ===")
    # Check GPU libraries
    from scripts.gpu_check import check_gpu_libs
    if not check_gpu_libs():
        logger.error("GPU library check failed. Exiting.")
        sys.exit(1)
    logger.info("Phase 2 completed: GPU check passed")

def run_phase_data_acquisition(logger: logging.Logger):
    """Run data acquisition phase."""
    logger.info("=== PHASE: DATA ACQUISITION ===")
    if not check_memory_usage(MEMORY_LIMIT_GB, "data_acquisition", logger):
        sys.exit(EXIT_CODE_MEMORY_LIMIT)
    
    fetch_vaers_data()
    logger.info("Phase completed: Data acquired")

def run_phase_3_cleaning(logger: logging.Logger):
    """Run Phase 3: Data Cleaning."""
    logger.info("=== PHASE 3: DATA CLEANING ===")
    if not check_memory_usage(CLEANING_MEMORY_LIMIT_GB, "data_cleaning", logger):
        sys.exit(EXIT_CODE_MEMORY_LIMIT)
    
    # Validate data first
    validate_data()
    
    # Clean data
    process_data()
    
    logger.info("Phase 3 completed: Data cleaned")

def run_phase_4_analysis(logger: logging.Logger):
    """Run Phase 4: Disproportionality Analysis."""
    logger.info("=== PHASE 4: DISPROPORTIONALITY ANALYSIS ===")
    if not check_memory_usage(ANALYSIS_MEMORY_LIMIT_GB, "analysis", logger):
        sys.exit(EXIT_CODE_MEMORY_LIMIT)
    
    # Run analysis
    results = run_analysis()
    
    # Generate signals CSV
    generate_signals_csv(results)
    
    logger.info("Phase 4 completed: Analysis done")

def run_phase_5_temporal(logger: logging.Logger):
    """Run Phase 5: Temporal Analysis."""
    logger.info("=== PHASE 5: TEMPORAL ANALYSIS ===")
    run_temporal_preparation()
    logger.info("Phase 5 completed: Temporal analysis done")

def run_phase_6_sensitivity(logger: logging.Logger):
    """Run Phase 6: Sensitivity Analysis."""
    logger.info("=== PHASE 6: SENSITIVITY ANALYSIS ===")
    run_sensitivity_analysis()
    generate_sensitivity_delta_csv()
    logger.info("Phase 6 completed: Sensitivity analysis done")

def run_full_pipeline(logger: logging.Logger):
    """Run the full pipeline with phase ordering."""
    logger.info("Starting full pipeline execution...")
    
    start_memory_profiling()
    
    try:
        run_phase_1_setup(logger)
        run_phase_2_validation(logger)
        run_phase_data_acquisition(logger)
        run_phase_3_cleaning(logger)
        run_phase_4_analysis(logger)
        run_phase_5_temporal(logger)
        run_phase_6_sensitivity(logger)
        
        peak_mem = stop_memory_profiling()
        logger.info(f"Pipeline completed successfully. Peak memory: {peak_mem:.2f} GB")
        
        # Save memory profile
        memory_profile = {
            "peak_memory_gb": round(peak_mem, 2),
            "limit_gb": MEMORY_LIMIT_GB,
            "status": "PASS" if peak_mem <= MEMORY_LIMIT_GB else "FAIL"
        }
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "memory_profile.json", "w") as f:
            json.dump(memory_profile, f, indent=2)
        
    except Exception as e:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4, 5, 6], help="Run specific phase")
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if args.full:
        run_full_pipeline(logger)
    elif args.phase:
        logger.info(f"Running Phase {args.phase} only")
        if args.phase == 1:
            run_phase_1_setup(logger)
        elif args.phase == 2:
            run_phase_2_validation(logger)
        elif args.phase == 3:
            run_phase_data_acquisition(logger)
            run_phase_3_cleaning(logger)
        elif args.phase == 4:
            run_phase_4_analysis(logger)
        elif args.phase == 5:
            run_phase_5_temporal(logger)
        elif args.phase == 6:
            run_phase_6_sensitivity(logger)
    else:
        logger.info("No action specified. Use --full or --phase N")
        sys.exit(1)

if __name__ == "__main__":
    main()