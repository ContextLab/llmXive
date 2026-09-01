"""
Main orchestration script for the alloy diffusion prediction pipeline.
Executes the full workflow: Ingestion -> Features -> Training -> Validation -> Reporting.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work regardless of execution context
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, DATA_DIR, MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOG_DIR
from utils.logging import get_logger, log_info, log_error_traceback
from data.acquisition import acquire_and_save_diffusion_data
from data.ingestion import load_and_filter, load_multiple_files, split_data_stratified
from data.curation import run_curation
from data.descriptors import compute_descriptors_dataframe
from models.training import prepare_features_target, train_random_forest, train_gradient_boosting, train_linear_regression, save_model_and_metrics
from models.save_artifacts import save_model_to_pickle, save_linear_coefficients
from models.inference import load_model, prepare_test_data, evaluate_model, run_inference
from validation.stats import run_validation_stats, save_validation_results
from validation.sensitivity import run_sensitivity_sweep
from validation.report_generator import generate_validation_report, save_report

def main():
    logger = get_logger(__name__)
    log_info(logger, "Starting Pipeline: Predicting Impact of Alloying on Diffusion Activation Energy")

    try:
        # 1. Setup Directories
        log_info(logger, "Ensuring directory structure...")
        ensure_directories()

        # 2. Data Acquisition (Check if raw data exists, fetch if not)
        raw_data_path = DATA_DIR / "raw" / "fetched_diffusion.csv"
        if not raw_data_path.exists():
            log_info(logger, "Raw data not found. Fetching from source...")
            acquire_and_save_diffusion_data()
        else:
            log_info(logger, f"Raw data found at {raw_data_path}. Skipping fetch.")

        # 3. Ingestion: Load and Filter
        log_info(logger, "Running Ingestion (Filtering for FCC Self-Diffusion)...")
        # load_and_filter expects to find the raw file or accepts a path
        # Based on task T013, it filters and saves to data/curated/filtered.csv eventually or intermediate
        # We assume load_and_filter handles the initial filter and returns a DF or saves it.
        # For orchestration, we call it to ensure the filtering happens.
        df_ingested = load_and_filter(raw_data_path)
        log_info(logger, f"Ingestion complete. Rows after filtering: {len(df_ingested)}")

        # 4. Curation: Handle missing values and log exclusions
        log_info(logger, "Running Curation (Handling missing values)...")
        df_curated, exclusions_log = run_curation(df_ingested)
        log_info(logger, f"Curation complete. Rows after curation: {len(df_curated)}")

        # 5. Feature Engineering: Compute Descriptors
        log_info(logger, "Computing Atomic Descriptors...")
        df_features = compute_descriptors_dataframe(df_curated)
        log_info(logger, f"Descriptors computed. Shape: {df_features.shape}")

        # 6. Model Training
        log_info(logger, "Starting Model Training (RF, GB, Linear)...")
        
        # Prepare X, y
        X, y = prepare_features_target(df_features)
        
        # Train Models
        rf_model, rf_metrics = train_random_forest(X, y)
        gb_model, gb_metrics = train_gradient_boosting(X, y)
        lr_model, lr_results = train_linear_regression(X, y)
        
        log_info(logger, "Model training complete.")

        # 7. Save Models and Metrics
        log_info(logger, "Saving models and artifacts...")
        
        # Save Pickles
        save_model_to_pickle(rf_model, "final_rf.pkl")
        save_model_to_pickle(gb_model, "final_gb.pkl")
        
        # Save Linear Coeffs
        save_linear_coefficients(lr_results)
        
        # 8. Inference & Evaluation (Compute final metrics on test set)
        log_info(logger, "Running Inference and Evaluation...")
        # Re-load test data logic or use the split from training if stored
        # The training module usually handles the split internally or returns it.
        # We assume run_inference or evaluate_model handles the final metrics calculation.
        # Based on T025, we need to save models/metrics.json
        # We will call the inference runner which aggregates RF and GB metrics.
        final_metrics = run_inference(rf_model, gb_model, X, y)
        
        log_info(logger, f"Final Metrics: {final_metrics}")

        # 9. Validation: Statistical Significance
        log_info(logger, "Running Statistical Validation...")
        stats_results = run_validation_stats(lr_results, X, y)
        save_validation_results(stats_results)

        # 10. Validation: Sensitivity Analysis
        log_info(logger, "Running Sensitivity Analysis...")
        sensitivity_results = run_sensitivity_sweep(df_features, rf_model, gb_model)

        # 11. Generate Final Report
        log_info(logger, "Generating Validation Report...")
        report_data = generate_validation_report(
            metrics=final_metrics,
            stats=stats_results,
            sensitivity=sensitivity_results
        )
        save_report(report_data)

        log_info(logger, "Pipeline execution completed successfully.")
        return 0

    except Exception as e:
        log_error_traceback(logger, e)
        return 1

if __name__ == "__main__":
    sys.exit(main())