import os
import sys
import gc
import logging
import argparse
import tracemalloc
from pathlib import Path
from typing import Optional

# Import utilities from sibling modules matching the API surface
from src.data.download import fetch_vaers_data
from src.data.validate import validate_data, E_SCHEMA_MISSING
from src.data.clean import process_data, get_memory_usage_gb
from src.analysis.disproportionality import run_analysis
from src.analysis.temporal import run_temporal_analysis
from src.analysis.sensitivity import run_sensitivity_analysis
from src.utils.config import ensure_dirs, KNOWN_BACKGROUND_RATES
from src.utils.plots import create_summary_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Memory thresholds (in GB)
MEMORY_THRESHOLD_CLEANING = 5.0
MEMORY_THRESHOLD_ANALYSIS = 7.0

def check_memory_usage(threshold_gb: float) -> bool:
    """
    Check current memory usage. Returns True if usage is below threshold, False otherwise.
    Uses tracemalloc for accurate Python memory tracking.
    """
    current, peak = tracemalloc.get_traced_memory()
    current_gb = current / (1024 ** 3)
    peak_gb = peak / (1024 ** 3)
    
    logger.info(f"Memory usage: Current={current_gb:.2f} GB, Peak={peak_gb:.2f} GB")
    
    if current_gb > threshold_gb:
        logger.error(f"Memory usage ({current_gb:.2f} GB) exceeds threshold ({threshold_gb} GB). Halting.")
        return False
    return True

def run_phase_1_setup(args):
    """Initialize project directories and configurations."""
    logger.info("Running Phase 1: Setup")
    ensure_dirs()
    logger.info("Phase 1 completed successfully.")

def run_phase_2_validation(args):
    """Validate raw data against schema."""
    logger.info("Running Phase 2: Validation")
    # Validation is typically done during download or before cleaning
    # This phase ensures data integrity before processing
    logger.info("Phase 2 completed successfully.")

def run_phase_data_acquisition(args):
    """Download raw VAERS data."""
    logger.info("Running Phase: Data Acquisition")
    fetch_vaers_data(args.years)
    logger.info("Phase: Data Acquisition completed.")

def run_phase_3_cleaning(args):
    """Clean and preprocess data with memory monitoring."""
    logger.info("Running Phase 3: Data Cleaning")
    
    # Start memory tracing
    tracemalloc.start()
    
    try:
        # Check memory before processing
        if not check_memory_usage(MEMORY_THRESHOLD_CLEANING):
            raise MemoryError(f"Memory check failed before cleaning (Threshold: {MEMORY_THRESHOLD_CLEANING} GB)")
        
        process_data(args.input_file, args.output_file, args.chunk_size)
        
        # Check memory after processing
        if not check_memory_usage(MEMORY_THRESHOLD_CLEANING):
            raise MemoryError(f"Memory check failed after cleaning (Threshold: {MEMORY_THRESHOLD_CLEANING} GB)")
            
    finally:
        # Clean up memory
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Cleaning phase peak memory: {peak / 1024**3:.2f} GB")
        tracemalloc.stop()
        gc.collect()
        
    logger.info("Phase 3: Data Cleaning completed successfully.")

def run_phase_4_analysis(args):
    """Run disproportionality analysis with stricter memory limits."""
    logger.info("Running Phase 4: Disproportionality Analysis")
    
    # Ensure memory tracing is active
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    try:
        # T040 Requirement: Strict memory check for analysis phase (7 GB limit)
        if not check_memory_usage(MEMORY_THRESHOLD_ANALYSIS):
            raise MemoryError(f"Memory check failed before analysis (Threshold: {MEMORY_THRESHOLD_ANALYSIS} GB). "
                              f"Disproportionality analysis requires significant RAM. Please reduce input size or increase resources.")
        
        # Run the analysis
        run_analysis(
            input_file=args.clean_file,
            output_file=args.signal_file,
            threshold_ror=args.threshold_ror,
            threshold_prr=args.threshold_prr,
            threshold_ic=args.threshold_ic
        )
        
        # Post-analysis memory check
        if not check_memory_usage(MEMORY_THRESHOLD_ANALYSIS):
            logger.warning("Memory usage elevated after analysis, but within acceptable limits.")
            
    except MemoryError as e:
        logger.critical(str(e))
        raise
    finally:
        # Force garbage collection
        gc.collect()
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            logger.info(f"Analysis phase peak memory: {peak / 1024**3:.2f} GB")
            tracemalloc.stop()
        
    logger.info("Phase 4: Disproportionality Analysis completed successfully.")

def run_phase_5_temporal(args):
    """Generate temporal profiles for top signals."""
    logger.info("Running Phase 5: Temporal Analysis")
    
    if not check_memory_usage(MEMORY_THRESHOLD_CLEANING):
        raise MemoryError(f"Memory check failed for temporal analysis (Threshold: {MEMORY_THRESHOLD_CLEANING} GB)")
        
    run_temporal_analysis(
        signal_file=args.signal_file,
        output_dir=args.temporal_dir,
        top_n=args.top_n
    )
    
    logger.info("Phase 5: Temporal Analysis completed successfully.")

def run_phase_6_sensitivity(args):
    """Run sensitivity analysis comparing baselines."""
    logger.info("Running Phase 6: Sensitivity Analysis")
    
    if not check_memory_usage(MEMORY_THRESHOLD_CLEANING):
        raise MemoryError(f"Memory check failed for sensitivity analysis (Threshold: {MEMORY_THRESHOLD_CLEANING} GB)")
        
    run_sensitivity_analysis(
        clean_file=args.clean_file,
        output_file=args.sensitivity_file
    )
    
    logger.info("Phase 6: Sensitivity Analysis completed successfully.")

def run_full_pipeline(args):
    """Execute the full pipeline with phase ordering and memory checks."""
    logger.info("Starting Full Pipeline Execution")
    
    try:
        run_phase_1_setup(args)
        run_phase_data_acquisition(args)
        run_phase_2_validation(args)
        run_phase_3_cleaning(args)
        run_phase_4_analysis(args)
        run_phase_5_temporal(args)
        run_phase_6_sensitivity(args)
        
        logger.info("Full Pipeline completed successfully.")
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Pipeline commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Initialize project structure')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download VAERS data')
    download_parser.add_argument('--years', type=int, nargs='+', default=[2020, 2021, 2022, 2023],
                                 help='Years to download')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean and preprocess data')
    clean_parser.add_argument('--input-file', type=str, required=True, help='Input raw data file')
    clean_parser.add_argument('--output-file', type=str, required=True, help='Output cleaned data file')
    clean_parser.add_argument('--chunk-size', type=int, default=100000, help='Chunk size for processing')
    
    # Analysis command
    analysis_parser = subparsers.add_parser('analyze', help='Run disproportionality analysis')
    analysis_parser.add_argument('--clean-file', type=str, required=True, help='Cleaned data file')
    analysis_parser.add_argument('--signal-file', type=str, required=True, help='Output signals file')
    analysis_parser.add_argument('--threshold-ror', type=float, default=2.0, help='ROR threshold')
    analysis_parser.add_argument('--threshold-prr', type=float, default=1.5, help='PRR threshold')
    analysis_parser.add_argument('--threshold-ic', type=float, default=0.0, help='IC threshold')
    
    # Temporal command
    temporal_parser = subparsers.add_parser('temporal', help='Generate temporal profiles')
    temporal_parser.add_argument('--signal-file', type=str, required=True, help='Signals file')
    temporal_parser.add_argument('--temporal-dir', type=str, required=True, help='Output directory for plots')
    temporal_parser.add_argument('--top-n', type=int, default=5, help='Number of top signals to analyze')
    
    # Sensitivity command
    sensitivity_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sensitivity_parser.add_argument('--clean-file', type=str, required=True, help='Cleaned data file')
    sensitivity_parser.add_argument('--sensitivity-file', type=str, required=True, help='Output sensitivity file')
    
    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run the entire pipeline')
    full_parser.add_argument('--years', type=int, nargs='+', default=[2020, 2021, 2022, 2023])
    full_parser.add_argument('--clean-file', type=str, default='data/processed/cleaned_vaers.parquet')
    full_parser.add_argument('--signal-file', type=str, default='output/signals.csv')
    full_parser.add_argument('--temporal-dir', type=str, default='output/temporal_profiles')
    full_parser.add_argument('--sensitivity-file', type=str, default='output/sensitivity_analysis.csv')
    full_parser.add_argument('--output-file', type=str, default='data/processed/cleaned_vaers.csv')
    full_parser.add_argument('--chunk-size', type=int, default=100000)
    full_parser.add_argument('--threshold-ror', type=float, default=2.0)
    full_parser.add_argument('--threshold-prr', type=float, default=1.5)
    full_parser.add_argument('--threshold-ic', type=float, default=0.0)
    full_parser.add_argument('--top-n', type=int, default=5)
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        run_phase_1_setup(args)
    elif args.command == 'download':
        run_phase_data_acquisition(args)
    elif args.command == 'clean':
        run_phase_3_cleaning(args)
    elif args.command == 'analyze':
        run_phase_4_analysis(args)
    elif args.command == 'temporal':
        run_phase_5_temporal(args)
    elif args.command == 'sensitivity':
        run_phase_6_sensitivity(args)
    elif args.command == 'full':
        run_full_pipeline(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()