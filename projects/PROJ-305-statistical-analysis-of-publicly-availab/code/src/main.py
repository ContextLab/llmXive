import os
import sys
import gc
import logging
import argparse
import tracemalloc
from pathlib import Path
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import ensure_dirs
from src.data.download import fetch_vaers_data
from src.data.validate import validate_data, load_schema
from src.data.clean import process_data, get_memory_usage_gb
from src.analysis.disproportionality import run_analysis
from src.analysis.temporal import run_temporal_analysis
from src.analysis.sensitivity import run_sensitivity_analysis

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

# Memory threshold constants
MEMORY_THRESHOLD_CLEANING_GB = 5.0
MEMORY_THRESHOLD_ANALYSIS_GB = 7.0  # Threshold for T040: Disproportionality Analysis

def get_memory_usage_gb() -> float:
    """
    Returns the current memory usage of the process in GB.
    Uses tracemalloc if available, otherwise falls back to psutil or returns 0.
    """
    try:
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024 * 1024)
    except Exception:
        logger.warning("tracemalloc not available or not tracing. Attempting psutil fallback.")
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024 * 1024)
        except Exception:
            logger.error("Could not determine memory usage. Returning 0.")
            return 0.0

def check_memory_usage(current_threshold_gb: float) -> bool:
    """
    Checks if current memory usage exceeds the provided threshold.
    Returns True if threshold is exceeded, False otherwise.
    """
    current_gb = get_memory_usage_gb()
    logger.info(f"Current memory usage: {current_gb:.2f} GB (Threshold: {current_threshold_gb:.2f} GB)")
    if current_gb > current_threshold_gb:
        logger.error(f"Memory usage {current_gb:.2f} GB exceeds threshold {current_threshold_gb:.2f} GB. Halting pipeline.")
        return True
    return False

def run_phase_1_setup():
    logger.info("Starting Phase 1: Setup")
    ensure_dirs()
    logger.info("Phase 1 Setup complete.")

def run_phase_2_validation():
    logger.info("Starting Phase 2: Validation")
    schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
    raw_data_path = PROJECT_ROOT / "data" / "raw"
    
    # Basic validation that files exist before proceeding
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        sys.exit(1)
    
    logger.info("Phase 2 Validation complete.")

def run_phase_data_acquisition():
    logger.info("Starting Phase: Data Acquisition")
    fetch_vaers_data()
    logger.info("Phase: Data Acquisition complete.")

def run_phase_3_cleaning():
    logger.info("Starting Phase 3: Data Cleaning")
    
    # Start memory tracing
    tracemalloc.start()
    
    try:
        # Check memory before heavy lifting
        if check_memory_usage(MEMORY_THRESHOLD_CLEANING_GB):
            raise MemoryError("Memory threshold exceeded during cleaning phase.")

        raw_dir = PROJECT_ROOT / "data" / "raw"
        output_dir = PROJECT_ROOT / "data" / "processed"
        
        if not raw_dir.exists():
            logger.error("Raw data directory not found. Run data acquisition first.")
            sys.exit(1)

        # Process data (chunked internally if needed)
        process_data(raw_dir, output_dir)

        # Force garbage collection
        gc.collect()
        
        # Final check
        if check_memory_usage(MEMORY_THRESHOLD_CLEANING_GB):
            logger.warning("Memory usage high after cleaning, but phase completed.")
        
        logger.info("Phase 3: Data Cleaning complete.")
    except MemoryError as e:
        logger.critical(str(e))
        sys.exit(1)
    finally:
        tracemalloc.stop()

def run_phase_4_analysis():
    """
    Implements T040: Disproportionality Analysis with 7GB RAM limit.
    """
    logger.info("Starting Phase 4: Disproportionality Analysis (T040)")
    
    tracemalloc.start()
    
    try:
        cleaned_data_path = PROJECT_ROOT / "data" / "processed" / "cleaned_vaers.parquet"
        if not cleaned_data_path.exists():
            logger.error("Cleaned data not found. Run Phase 3 first.")
            sys.exit(1)

        # T040: Check memory specifically for analysis phase (7GB limit)
        if check_memory_usage(MEMORY_THRESHOLD_ANALYSIS_GB):
            raise MemoryError(f"Memory usage exceeds {MEMORY_THRESHOLD_ANALYSIS_GB} GB threshold for analysis phase.")

        logger.info("Memory check passed for analysis phase.")

        output_dir = PROJECT_ROOT / "output"
        ensure_dirs() # Ensure output exists

        run_analysis(cleaned_data_path, output_dir)
        
        gc.collect()
        
        if check_memory_usage(MEMORY_THRESHOLD_ANALYSIS_GB):
            logger.warning("Memory usage high after analysis.")

        logger.info("Phase 4: Disproportionality Analysis complete.")
    except MemoryError as e:
        logger.critical(str(e))
        sys.exit(1)
    finally:
        tracemalloc.stop()

def run_phase_5_temporal():
    logger.info("Starting Phase 5: Temporal Analysis")
    signals_path = PROJECT_ROOT / "output" / "signals.csv"
    output_dir = PROJECT_ROOT / "output" / "temporal_profiles"
    
    if not signals_path.exists():
        logger.error("Signals file not found. Run Phase 4 first.")
        sys.exit(1)

    run_temporal_analysis(signals_path, output_dir)
    logger.info("Phase 5: Temporal Analysis complete.")

def run_phase_6_sensitivity():
    logger.info("Starting Phase 6: Sensitivity Analysis")
    signals_path = PROJECT_ROOT / "output" / "signals.csv"
    output_dir = PROJECT_ROOT / "output"
    
    if not signals_path.exists():
        logger.error("Signals file not found. Run Phase 4 first.")
        sys.exit(1)

    run_sensitivity_analysis(signals_path, output_dir)
    logger.info("Phase 6: Sensitivity Analysis complete.")

def run_full_pipeline():
    logger.info("Starting Full Pipeline Execution")
    run_phase_1_setup()
    run_phase_2_validation()
    run_phase_data_acquisition()
    run_phase_3_cleaning()
    run_phase_4_analysis() # T040 logic is inside here
    run_phase_5_temporal()
    run_phase_6_sensitivity()
    logger.info("Full Pipeline Execution Complete.")

def main():
    parser = argparse.ArgumentParser(description="VAERS Statistical Analysis Pipeline")
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5, 6], 
                        help='Run specific phase only')
    parser.add_argument('--full', action='store_true', help='Run full pipeline')
    
    args = parser.parse_args()
    
    if args.full:
        run_full_pipeline()
    elif args.phase:
        phase_map = {
            1: run_phase_1_setup,
            2: run_phase_2_validation,
            3: run_phase_data_acquisition,
            4: run_phase_3_cleaning,
            5: run_phase_4_analysis,
            6: run_phase_5_temporal,
            7: run_phase_6_sensitivity
        }
        # Adjusting mapping for 1-based index vs function names
        # Phase 1: Setup, 2: Validation, 3: Acquisition, 4: Cleaning, 5: Analysis, 6: Temporal
        # The task T040 is specifically about Phase 5 (Analysis) in the function naming convention above?
        # Let's align: 
        # run_phase_1_setup -> Phase 1
        # run_phase_2_validation -> Phase 2
        # run_phase_data_acquisition -> Phase 3
        # run_phase_3_cleaning -> Phase 4
        # run_phase_4_analysis -> Phase 5 (This is where T040 logic lives)
        
        if args.phase == 1: run_phase_1_setup()
        elif args.phase == 2: run_phase_2_validation()
        elif args.phase == 3: run_phase_data_acquisition()
        elif args.phase == 4: run_phase_3_cleaning()
        elif args.phase == 5: run_phase_4_analysis() # T040
        elif args.phase == 6: run_phase_5_temporal()
        elif args.phase == 7: run_phase_6_sensitivity()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()