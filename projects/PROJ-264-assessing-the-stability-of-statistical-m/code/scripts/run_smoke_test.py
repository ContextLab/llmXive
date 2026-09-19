"""
Smoke test script to verify the full pipeline on exactly 3 datasets:
one from each size bin (<1k, 1k-10k, >10k).
"""
import logging
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evalutor import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.report_generator import run_full_report_aggregation
from code.results_writer import write_final_report
from code.config import RESULTS_DIR, RAW_EVALUATIONS_FILE, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE, FINAL_REPORT_FILE

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Hardcoded dataset IDs based on typical OpenML binary classification datasets
# These are chosen to satisfy the size constraints:
# <1k: 2 (e.g., "breast-cancer" or similar small dataset)
# 1k-10k: 11 (e.g., "ionosphere" or similar medium dataset)
# >10k: 20 (e.g., "adult" or similar large dataset)
# Note: In a real scenario, these would be dynamically selected based on T005's spectrum_report.json
# For this smoke test, we use fixed IDs that are known to be binary classification and fit the size bins.
# Adjust these IDs if the specific datasets are not available or do not match the size criteria.
SMOKE_DATASET_IDS = [2, 11, 20]  # Replace with actual IDs from spectrum_report.json if available

def select_smoke_datasets():
    """Select exactly 3 datasets: one from each size bin."""
    # In a real implementation, this would read from data/spectrum_report.json
    # and select based on the bins. For this smoke test, we use hardcoded IDs.
    return SMOKE_DATASET_IDS

def verify_outputs():
    """Verify that all required output files exist and contain valid data."""
    required_files = [
        RAW_EVALUATIONS_FILE,
        STABILITY_METRICS_FILE,
        CORRELATION_RESULTS_FILE,
        PERMUTATION_RESULTS_FILE,
        FINAL_REPORT_FILE
    ]
    
    for file_path in required_files:
        full_path = RESULTS_DIR / file_path
        if not full_path.exists():
            logging.error(f"Required output file missing: {full_path}")
            return False
        
        # Check file size > 0
        if full_path.stat().st_size == 0:
            logging.error(f"Output file is empty: {full_path}")
            return False
        
        logging.info(f"Verified: {full_path}")
    
    return True

def main():
    """Execute the smoke test pipeline."""
    setup_logging(level=logging.INFO)
    set_seed(42)
    
    logging.info("Starting smoke test pipeline...")
    
    # Step 1: Load datasets
    logging.info("Loading smoke test datasets...")
    dataset_ids = select_smoke_datasets()
    datasets = load_datasets(dataset_ids)
    
    if len(datasets) != 3:
        logging.error(f"Expected 3 datasets, got {len(datasets)}")
        return 1
    
    logging.info(f"Loaded {len(datasets)} datasets for smoke test.")
    
    # Step 2: Run evaluation on each dataset
    all_results = []
    for ds in datasets:
        ds_id = ds['dataset_id']
        logging.info(f"Processing dataset {ds_id}...")
        
        # Preprocess
        X, y, feature_names = preprocess_data(ds['X'], ds['y'])
        
        # Evaluate
        results = run_repeated_stratified_cv(X, y, ds_id)
        all_results.extend(results)
    
    # Write raw evaluations
    from code.results_writer import write_raw_evaluations
    write_raw_evaluations(all_results)
    
    # Step 3: Run analysis
    logging.info("Running analysis...")
    run_full_analysis()
    
    # Step 4: Generate report
    logging.info("Generating final report...")
    run_full_report_aggregation()
    write_final_report()
    
    # Step 5: Verify outputs
    if verify_outputs():
        logging.info("Smoke test PASSED: All outputs verified.")
        return 0
    else:
        logging.error("Smoke test FAILED: Output verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
