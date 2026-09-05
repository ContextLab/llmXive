import os
import sys
import logging
import time
from pathlib import Path
import json

from config import ensure_directories, set_global_seed, DATA_DIR, MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOG_DIR
from utils.logging import get_logger, log_info, log_error_traceback
from data.acquisition import acquire_and_save_diffusion_data
from data.ingestion import load_and_filter, split_data_stratified
from data.curation import run_curation
from data.descriptors import compute_descriptors_dataframe
from models.training import prepare_features_target, train_random_forest, train_gradient_boosting, train_linear_regression, save_model_and_metrics
from models.inference import run_inference
from models.save_artifacts import save_linear_coefficients, aggregate_metrics
from validation.stats import run_validation_stats, save_validation_results
from validation.sensitivity import run_sensitivity_sweep, calculate_stability_metric, save_sensitivity_sweep_csv
from validation.report_generator import generate_validation_report, save_report

logger = get_logger(__name__)

def main():
    """
    Orchestrate the full pipeline: Ingestion -> Features -> Training -> Validation
    """
    start_time = time.time()
    set_global_seed()
    ensure_directories()
    
    log_info("Starting full pipeline execution...")

    try:
        # Phase 2/3: Data Acquisition and Ingestion
        log_info("Step 1: Acquiring real diffusion data...")
        acquire_and_save_diffusion_data()
        
        log_info("Step 2: Ingesting and filtering data...")
        df_raw = load_and_filter()
        if df_raw is None or df_raw.empty:
            raise ValueError("Ingestion produced no data.")
        
        log_info("Step 3: Curing data (handling missing values)...")
        df_curated = run_curation(df_raw)
        if df_curated is None or df_curated.empty:
            raise ValueError("Curation produced no data.")

        # Phase 4: Feature Engineering
        log_info("Step 4: Computing descriptors...")
        df_features = compute_descriptors_dataframe(df_curated)
        
        # Split data
        X, y = prepare_features_target(df_features)
        X_train, X_test, y_train, y_test = split_data_stratified(X, y)

        # Phase 4: Model Training
        log_info("Step 5: Training Random Forest...")
        rf_model, rf_metrics = train_random_forest(X_train, y_train)
        save_model_and_metrics(rf_model, "final_rf.pkl", rf_metrics)
        
        log_info("Step 6: Training Gradient Boosting...")
        gb_model, gb_metrics = train_gradient_boosting(X_train, y_train)
        save_model_and_metrics(gb_model, "final_gb.pkl", gb_metrics)
        
        log_info("Step 7: Training Linear Regression...")
        lr_model, lr_metrics, lr_coef, lr_intercept, lr_p_value = train_linear_regression(X_train, y_train)
        save_model_and_metrics(lr_model, "linear_model.pkl", lr_metrics)
        
        # Save Linear Regression coefficients specifically for T024
        save_linear_coefficients(lr_coef, lr_intercept, lr_p_value)

        # Phase 4: Inference and Metrics Aggregation
        log_info("Step 8: Evaluating models on test set...")
        rf_test_metrics = run_inference(rf_model, X_test, y_test, "rf")
        gb_test_metrics = run_inference(gb_model, X_test, y_test, "gb")
        
        # Calculate Mean Predictor R2
        mean_pred = y_train.mean()
        mean_r2 = 1 - (np.sum((y_test - mean_pred) ** 2) / np.sum((y_test - y_test.mean()) ** 2))
        
        # Aggregate all metrics (T024 requirement)
        aggregate_metrics(
            rf_metrics=rf_test_metrics,
            gb_metrics=gb_test_metrics,
            mean_r2=mean_r2,
            linear_metrics=lr_metrics
        )

        # Phase 5: Statistical Validation
        log_info("Step 9: Running statistical validation...")
        validation_results = run_validation_stats(lr_coef, lr_p_value, X_train, y_train)
        save_validation_results(validation_results)

        # Phase 5: Sensitivity Analysis
        log_info("Step 10: Running sensitivity analysis...")
        # Note: T031 is assumed to have run or is integrated here if not a separate task execution
        # Assuming baseline_shifts.csv exists from T031 logic or is generated here for flow
        # For this orchestration, we assume the data is ready or generated in the flow if T031 is skipped
        # In a strict sequential run, T031 would run before T032.
        
        # Run sweep (T032)
        run_sensitivity_sweep()
        
        # Calculate stability (T033)
        stability = calculate_stability_metric()
        
        # Generate final report (T034)
        report_data = generate_validation_report(
            rf_metrics=rf_test_metrics,
            gb_metrics=gb_test_metrics,
            mean_r2=mean_r2,
            validation_results=validation_results,
            stability_metrics=stability
        )
        save_report(report_data)

        end_time = time.time()
        runtime = end_time - start_time
        log_info(f"Pipeline completed successfully in {runtime:.2f} seconds.")
        
        # Log runtime for performance check (T038)
        perf_log = {"total_runtime_seconds": runtime}
        with open(Path(REPORTS_DIR) / "performance_log.json", 'w') as f:
            json.dump(perf_log, f, indent=4)

    except Exception as e:
        log_error_traceback(e)
        sys.exit(1)

if __name__ == "__main__":
    main()