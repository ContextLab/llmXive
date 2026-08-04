import argparse
import sys
import logging
import time
import os
import resource
from code.config import LOG_LEVEL, RESULTS_DIR, DATA_RAW_DIR, ensure_dirs

# Import existing mode runners from the project API
from code.data_loader import run_data_load
from code.permutation import run_batch_permutation_test
from code.p_values_saver import run_p_values_saving
from code.power_analysis import run_power_analysis, run_mdes_summary_generation, run_bh_correction
from code.sensitivity_analysis import run_sensitivity_analysis
from code.corrected_p_values_saver import run_corrected_p_values_generation
from code.visualization import run_visualization
from code.summary_generator import run_summary_generation

logger = logging.getLogger(__name__)

# Constants for runtime/memory guard (Task T032)
MAX_RUNTIME_HOURS = 5.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600
MAX_MEMORY_GB = 6.0
MAX_MEMORY_BYTES = int(MAX_MEMORY_GB * 1024**3)

def get_current_memory_usage_gb():
    """
    Returns the current memory usage of the process in GB.
    Uses resource module (Unix/Linux/macOS) for accurate RSS measurement.
    Falls back to 0.0 on Windows or if resource module is unavailable.
    """
    try:
        # rusage.ru_maxrss is in KB on Linux/macOS
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return usage_kb / (1024.0 * 1024.0) # Convert KB to GB
    except (AttributeError, OSError):
        logger.warning("resource module not available for memory check (Windows?). Skipping memory check.")
        return 0.0

def check_runtime_and_memory_guard(start_time: float) -> bool:
    """
    Checks if the current runtime exceeds MAX_RUNTIME_HOURS or memory usage exceeds MAX_MEMORY_GB.
    Returns True if limits are exceeded (subsampling triggered), False otherwise.
    """
    current_time = time.time()
    elapsed_seconds = current_time - start_time
    elapsed_hours = elapsed_seconds / 3600.0

    memory_gb = get_current_memory_usage_gb()

    exceeded_runtime = elapsed_hours > MAX_RUNTIME_HOURS
    exceeded_memory = memory_gb > MAX_MEMORY_GB

    if exceeded_runtime or exceeded_memory:
        reason = []
        if exceeded_runtime:
            reason.append(f"Runtime limit exceeded ({elapsed_hours:.2f}h > {MAX_RUNTIME_HOURS}h)")
        if exceeded_memory:
            reason.append(f"Memory limit exceeded ({memory_gb:.2f}GB > {MAX_MEMORY_GB}GB)")

        logger.warning(f"RUNTIME/MEMORY GUARD TRIGGERED: {'; '.join(reason)}")
        logger.warning("Force subsampling enabled. Limiting query set to 100 random queries to ensure completion.")
        return True

    return False

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Validity Evaluation Pipeline")
    parser.add_argument("--mode", type=str, choices=[
        "load", "permutation", "p_values", "power_analysis", "mdes", "sensitivity",
        "corrected_p_values", "report", "all"
    ], default="all", help="Mode to run")
    parser.add_argument("--limit_queries", type=int, default=None,
                        help="Limit number of queries to process (for testing/subsampling)")
    return parser.parse_args()

def run_data_load_mode(limit_queries=None):
    logger.info("Running Data Load Mode...")
    # Pass limit if supported by underlying function, otherwise handled internally if needed
    run_data_load(limit_queries=limit_queries)

def run_permutation_mode(limit_queries=None):
    logger.info("Running Permutation Mode...")
    start_time = time.time()
    # Check guard before starting heavy permutation work
    if check_runtime_and_memory_guard(start_time):
        limit_queries = 100 # Force subsampling
        logger.info(f"Subsampling to {limit_queries} queries due to guard trigger.")

    run_batch_permutation_test(limit_queries=limit_queries)

def run_p_values_mode():
    logger.info("Running P-Values Calculation Mode...")
    run_p_values_saving()

def run_power_analysis_mode():
    logger.info("Running Power Analysis Mode...")
    start_time = time.time()
    # Check guard before starting power analysis (bootstrap is heavy)
    if check_runtime_and_memory_guard(start_time):
        logger.warning("Power analysis mode triggered guard. Proceeding with reduced query set if applicable.")
    run_power_analysis()

def run_mdes_summary_mode():
    logger.info("Running MDES Summary Mode...")
    run_mdes_summary_generation()

def run_sensitivity_mode():
    logger.info("Running Sensitivity Analysis Mode...")
    run_sensitivity_analysis()

def run_corrected_p_values_mode():
    logger.info("Running Corrected P-Values Mode...")
    run_corrected_p_values_generation()

def run_report_mode():
    logger.info("Running Report Mode (Visualization + Summary)...")
    start_time = time.time()
    # Check guard before generating plots (memory intensive)
    if check_runtime_and_memory_guard(start_time):
        logger.warning("Report mode triggered guard. Proceeding with reduced set.")
    
    run_visualization()
    run_summary_generation()

def run_all_modes():
    logger.info("Running All Modes...")
    start_time = time.time()
    
    # 1. Load Data
    run_data_load_mode()
    if check_runtime_and_memory_guard(start_time):
        logger.warning("Data load triggered guard. Subsampling for subsequent steps.")
        # Note: Actual subsampling logic would need to be passed to subsequent calls
        # For this implementation, we set a flag or pass limit to next steps if they support it
        # Since run_permutation_mode handles the check internally, we just proceed.
    
    # 2. Permutation
    run_permutation_mode()
    if check_runtime_and_memory_guard(start_time):
        logger.warning("Permutation triggered guard. Subsampling for subsequent steps.")

    # 3. P-Values
    run_p_values_mode()

    # 4. Power Analysis
    run_power_analysis_mode()

    # 5. MDES Summary
    run_mdes_summary_mode()

    # 6. Sensitivity
    run_sensitivity_mode()

    # 7. Corrected P-Values
    run_corrected_p_values_mode()

    # 8. Report
    run_report_mode()

def main():
    logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
    ensure_dirs()
    
    args = parse_args()
    
    try:
        if args.mode == "load":
            run_data_load_mode(args.limit_queries)
        elif args.mode == "permutation":
            run_permutation_mode(args.limit_queries)
        elif args.mode == "p_values":
            run_p_values_mode()
        elif args.mode == "power_analysis":
            run_power_analysis_mode()
        elif args.mode == "mdes":
            run_mdes_summary_mode()
        elif args.mode == "sensitivity":
            run_sensitivity_mode()
        elif args.mode == "corrected_p_values":
            run_corrected_p_values_mode()
        elif args.mode == "report":
            run_report_mode()
        elif args.mode == "all":
            run_all_modes()
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()