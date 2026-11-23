"""
Smoke Test Script for PROJ-264
Executes the full pipeline on exactly 3 datasets (one from each size bin)
and verifies that all expected output artifacts are generated.
"""
import logging
import os
import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evaluator import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.report_generator import run_full_report_aggregation
from code.results_writer import write_final_report

# Constants
SMOKE_DATASET_IDS = [
    59,    # < 1k (Iris subset or similar small dataset)
    14,    # 1k-10k (Heart-statlog)
    1461   # > 10k (Credit-a)
]
# Note: IDs selected based on T050a spec: iris (59), heart-statlog (14), credit-a (1461)
# If specific IDs change based on availability, update here.

# Ensure paths exist
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

def select_smoke_datasets():
    """Returns the hardcoded list of 3 dataset IDs."""
    return SMOKE_DATASET_IDS

def verify_outputs():
    """
    Verifies that all required output files exist and contain data.
    Returns True if all checks pass, False otherwise.
    """
    required_files = [
        "results/raw_evaluations.csv",
        "results/stability_metrics.csv",
        "results/correlation_results.csv",
        "results/permutation_results.csv",
        "results/final_report.md"
    ]
    
    all_valid = True
    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            logging.error(f"Missing required output file: {file_path}")
            all_valid = False
            continue
        
        # Check file size > 0
        if path.stat().st_size == 0:
            logging.error(f"Output file is empty: {file_path}")
            all_valid = False
            continue
        
        logging.info(f"Verified: {file_path} (size: {path.stat().st_size} bytes)")
    
    return all_valid

def main():
    """Orchestrates the smoke test execution."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting Smoke Test Execution (T050b)")
    logger.info("=" * 60)
    
    # 1. Setup
    set_seed(42)
    dataset_ids = select_smoke_datasets()
    logger.info(f"Selected datasets for smoke test: {dataset_ids}")
    
    # 2. Load Data
    logger.info("Loading datasets...")
    try:
        datasets = load_datasets(dataset_ids)
        if not datasets:
            logger.error("No datasets loaded. Exiting.")
            return 1
        logger.info(f"Successfully loaded {len(datasets)} datasets.")
    except Exception as e:
        logger.error(f"Failed to load datasets: {e}")
        return 1
    
    # 3. Run Evaluation
    logger.info("Starting repeated stratified CV evaluation...")
    start_time = time.time()
    
    try:
        # Run evaluation for all loaded datasets
        # Note: run_repeated_stratified_cv is expected to return raw evaluations dataframe
        raw_evals = run_repeated_stratified_cv(datasets)
        
        elapsed = time.time() - start_time
        logger.info(f"Evaluation completed in {elapsed:.2f} seconds.")
        logger.info(f"Generated {len(raw_evals)} raw evaluation records.")
        
        # 4. Run Analysis
        logger.info("Running analysis (aggregation, correlation, permutation)...")
        analysis_results = run_full_analysis(raw_evals)
        
        # 5. Generate Report
        logger.info("Generating final report...")
        report_data = run_full_report_aggregation(analysis_results)
        write_final_report(report_data)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1
    
    # 6. Verify Outputs
    logger.info("Verifying output artifacts...")
    if verify_outputs():
        logger.info("Smoke Test PASSED: All outputs generated and valid.")
        return 0
    else:
        logger.error("Smoke Test FAILED: Missing or invalid outputs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())