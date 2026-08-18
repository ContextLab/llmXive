"""
Smoke Test Script for T050: Final End-to-End Smoke Test.

Executes the full pipeline on exactly 3 datasets (one from each size bin)
to verify the entire flow from download to final report generation.

Datasets selected:
- Small (<1k): Breast Cancer (OpenML ID: 2) - ~569 samples
- Medium (1k-10k): Ionosphere (OpenML ID: 29) - ~351 samples (Wait, <1k. Need medium)
- Medium (1k-10k): SPECT Heart (OpenML ID: 31) - ~260 (Too small). Let's use:
  - Small: Breast Cancer (ID: 2) [569] -> Wait, 569 is < 1k. Good.
  - Medium: Ionosphere (ID: 29) [351] -> < 1k. Bad.
  - Medium: Pima Indians (ID: 187) [768] -> < 1k. Bad.
  - Medium: Heart (ID: 14) [270] -> < 1k. Bad.
  - Medium: Sonar (ID: 80) [208] -> < 1k. Bad.
  - Medium: Splice (ID: 132) [3190] -> 1k-10k. Good.
  - Large (>10k): Adult (ID: 1590) [48842] -> >10k. Good.

Selected IDs:
1. Splice (ID: 132) -> Medium (3190 samples)
2. Adult (ID: 1590) -> Large (48842 samples)
3. Breast Cancer (ID: 2) -> Small (569 samples)

Note: The task requires one from each bin.
Bin 1 (<1k): Breast Cancer (ID: 2) [569]
Bin 2 (1k-10k): Splice (ID: 132) [3190]
Bin 3 (>10k): Adult (ID: 1590) [48842]

This script orchestrates the execution of the pipeline components in the correct order.
"""
import os
import sys
import logging
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.evaluator import run_repeated_stratified_cv
from code.analyser import (
    aggregate_stability_metrics,
    calculate_correlations,
    run_permutation_test,
    apply_global_bh_correction,
    calculate_log_log_regression
)
from code.results_writer import (
    write_raw_evaluations,
    write_stability_metrics,
    write_correlation_results,
    write_permutation_results,
    write_final_report
)
from code.report_generator import run_full_report_aggregation

# Constants
SMOKE_DATASETS = {
    "small": 2,       # Breast Cancer (~569)
    "medium": 132,    # Splice (~3190)
    "large": 1590     # Adult (~48842)
}

MODEL_NAMES = ["LogisticRegression", "RandomForest", "LinearSVM"]
SEED = 42
RESULTS_DIR = project_root / "results"

def log_header(msg):
    logging.info("=" * 60)
    logging.info(msg)
    logging.info("=" * 60)

def calculate_file_hash(filepath):
    if not filepath.exists():
        return None
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main():
    setup_logging(level=logging.INFO)
    set_seed(SEED)
    
    RESULTS_DIR.mkdir(exist_ok=True)
    
    log_header("Starting Smoke Test (T050)")
    logging.info(f"Selected Datasets: {SMOKE_DATASETS}")
    
    # 1. Load Datasets
    log_header("Step 1: Loading Datasets")
    dataset_ids = list(SMOKE_DATASETS.values())
    datasets_info = load_datasets(dataset_ids)
    
    if len(datasets_info) != 3:
        logging.error("Failed to load exactly 3 datasets.")
        sys.exit(1)
    
    logging.info(f"Loaded {len(datasets_info)} datasets successfully.")
    
    # 2. Run Evaluation
    log_header("Step 2: Running Repeated Stratified CV")
    all_raw_results = []
    
    for ds_info in datasets_info:
        ds_id = ds_info['dataset_id']
        X, y = ds_info['X'], ds_info['y']
        logging.info(f"Evaluating dataset {ds_id} (n={len(y)})...")
        
        try:
            results_df = run_repeated_stratified_cv(X, y, MODEL_NAMES, seed=SEED)
            results_df['dataset_id'] = ds_id
            all_raw_results.append(results_df)
            logging.info(f"Completed dataset {ds_id}. Generated {len(results_df)} rows.")
        except Exception as e:
            logging.error(f"Error evaluating dataset {ds_id}: {e}")
            raise
    
    if not all_raw_results:
        logging.error("No evaluation results generated.")
        sys.exit(1)
        
    raw_df = pd.concat(all_raw_results, ignore_index=True)
    raw_output_path = RESULTS_DIR / "raw_evaluations.csv"
    write_raw_evaluations(raw_df, raw_output_path)
    logging.info(f"Raw evaluations written to {raw_output_path}")
    
    # 3. Aggregate Stability Metrics
    log_header("Step 3: Aggregating Stability Metrics")
    stability_df = aggregate_stability_metrics(raw_df)
    stability_output_path = RESULTS_DIR / "stability_metrics.csv"
    write_stability_metrics(stability_df, stability_output_path)
    logging.info(f"Stability metrics written to {stability_output_path}")
    
    # 4. Calculate Correlations
    log_header("Step 4: Calculating Correlations")
    # Load dataset properties for correlation
    # We construct properties from the loaded datasets info
    properties = []
    for ds_info in datasets_info:
        properties.append({
            'dataset_id': ds_info['dataset_id'],
            'n_samples': len(ds_info['y']),
            'n_features': ds_info['X'].shape[1]
        })
    props_df = pd.DataFrame(properties)
    
    corr_df = calculate_correlations(stability_df, props_df)
    corr_output_path = RESULTS_DIR / "correlation_results.csv"
    write_correlation_results(corr_df, corr_output_path)
    logging.info(f"Correlation results written to {corr_output_path}")
    
    # 5. Run Permutation Tests
    log_header("Step 5: Running Permutation Tests")
    perm_df = run_permutation_test(raw_df)
    perm_output_path = RESULTS_DIR / "permutation_results.csv"
    write_permutation_results(perm_df, perm_output_path)
    logging.info(f"Permutation results written to {perm_output_path}")
    
    # 6. Apply Global Holm-Bonferroni Correction
    log_header("Step 6: Applying Global Holm-Bonferroni Correction")
    # Re-load to ensure we have the latest data if functions modify in-place
    corr_final = pd.read_csv(corr_output_path)
    perm_final = pd.read_csv(perm_output_path)
    
    # Combine p-values for global correction
    corr_final, perm_final = apply_global_bh_correction(corr_final, perm_final)
    
    # Write updated files
    write_correlation_results(corr_final, corr_output_path)
    write_permutation_results(perm_final, perm_output_path)
    logging.info("Global correction applied and files updated.")
    
    # 7. Calculate Log-Log Regression & Residuals (T019b/T020)
    log_header("Step 7: Calculating Log-Log Regression & Residuals")
    regression_df, residuals_df = calculate_log_log_regression(stability_df, props_df)
    regression_path = RESULTS_DIR / "regression_coefficients.csv"
    residuals_path = RESULTS_DIR / "theoretical_deviation.csv"
    
    regression_df.to_csv(regression_path, index=False)
    residuals_df.to_csv(residuals_path, index=False)
    logging.info(f"Regression coefficients written to {regression_path}")
    logging.info(f"Residuals written to {residuals_path}")
    
    # 8. Update Correlation Results with Adjusted P-values (T021)
    log_header("Step 8: Finalizing Summary Tables (T021)")
    # Re-read stability metrics to ensure log_cv is present if calculated there
    # The aggregate_stability_metrics should have calculated log_cv.
    # We need to ensure correlation_results has the final state.
    # The apply_global_bh_correction already updated them, but we write again to be safe.
    write_correlation_results(corr_final, corr_output_path)
    
    # 9. Generate Final Report
    log_header("Step 9: Generating Final Report")
    report_data = run_full_report_aggregation(
        stability_df, 
        corr_final, 
        perm_final
    )
    report_path = RESULTS_DIR / "final_report.md"
    write_final_report(report_data, report_path)
    logging.info(f"Final report written to {report_path}")
    
    # 10. Validation
    log_header("Step 10: Validating Outputs")
    required_files = [
        "raw_evaluations.csv",
        "stability_metrics.csv",
        "correlation_results.csv",
        "permutation_results.csv",
        "final_report.md",
        "regression_coefficients.csv",
        "theoretical_deviation.csv"
    ]
    
    all_valid = True
    for fname in required_files:
        fpath = RESULTS_DIR / fname
        if not fpath.exists():
            logging.error(f"MISSING: {fname}")
            all_valid = False
        else:
            size = fpath.stat().st_size
            if size == 0:
                logging.error(f"EMPTY: {fname}")
                all_valid = False
            else:
                logging.info(f"OK: {fname} ({size} bytes)")
    
    if not all_valid:
        logging.error("Smoke Test FAILED: Missing or empty files.")
        sys.exit(1)
        
    # Verify data content
    logging.info("Verifying data content...")
    
    # Check raw_evaluations has variance
    raw_check = pd.read_csv(RESULTS_DIR / "raw_evaluations.csv")
    if raw_check['accuracy'].std() == 0:
        logging.warning("WARNING: No variance in raw accuracy scores (expected for very small/smooth data, but rare).")
    else:
        logging.info("Variance detected in raw evaluations.")
        
    # Check correlation results has p-values
    corr_check = pd.read_csv(RESULTS_DIR / "correlation_results.csv")
    if 'adj_p_value_holm' not in corr_check.columns:
        logging.error("Missing 'adj_p_value_holm' in correlation results.")
        all_valid = False
        
    # Check permutation results has p-values
    perm_check = pd.read_csv(RESULTS_DIR / "permutation_results.csv")
    if 'adj_p_value_holm' not in perm_check.columns:
        logging.error("Missing 'adj_p_value_holm' in permutation results.")
        all_valid = False
        
    if all_valid:
        logging.info("Smoke Test PASSED successfully.")
        sys.exit(0)
    else:
        logging.error("Smoke Test FAILED validation checks.")
        sys.exit(1)

if __name__ == "__main__":
    main()
