"""
Main orchestration script for the Coating Adhesion Strength Prediction Pipeline.
Executes the full workflow: Data Gap Check -> Ingestion -> Preprocessing -> Modeling -> Evaluation.
"""
import os
import sys
import logging
import yaml
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import local modules based on API surface
from utils import (
    check_halt_signal, write_halt_signal,
    verify_materials_project_and_halt, verify_nist_repository_and_halt,
    calculate_exclusion_ratio, calculate_processing_success_rate
)
from ingestion import process_ingestion_data
from preprocessing import (
    encode_compositional_data, standardize_surface_metrics,
    perform_construct_validity_check, main as preprocessing_main
)
from modeling import run_modeling_pipeline, run_sensitivity_analysis_crosslinker_proxy
from evaluation import run_baseline_evaluation_pipeline
from state_manager import write_state_file
from utils import log_memory_snapshot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
STATE_DIR = PROJECT_ROOT / 'state'
FIGURES_DIR = PROJECT_ROOT / 'figures'

def check_halt_signal():
    """Check if a halt signal exists from Phase 0 or previous steps."""
    return check_halt_signal(STATE_DIR)

def calculate_validation_metrics(raw_data_path, processed_data_path):
    """
    Calculate exclusion ratio and processing success rate.
    Returns a dict with metrics.
    """
    if not os.path.exists(raw_data_path):
        logger.warning(f"Raw data path not found: {raw_data_path}")
        return {"exclusion_ratio": 1.0, "success_rate": 0.0}
    
    try:
        # Load raw and processed to calculate metrics
        # Assuming raw data is a list of files or a directory structure
        # For this implementation, we assume a summary file or direct count
        # In a real scenario, this would scan the raw directory
        exclusion_ratio = calculate_exclusion_ratio(raw_data_path, processed_data_path)
        success_rate = calculate_processing_success_rate(raw_data_path, processed_data_path)
        return {
            "exclusion_ratio": exclusion_ratio,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"Error calculating validation metrics: {e}")
        return {"exclusion_ratio": 1.0, "success_rate": 0.0}

def enforce_validation_gate(metrics):
    """
    Enforce safety gates:
    - Exclusion ratio < 10%
    - Success rate >= 95%
    """
    if metrics["exclusion_ratio"] >= 0.10:
        logger.error(f"Exclusion ratio {metrics['exclusion_ratio']:.2%} exceeds 10% threshold.")
        write_halt_signal(STATE_DIR, "Exclusion ratio too high")
        return False
    
    if metrics["success_rate"] < 0.95:
        logger.error(f"Success rate {metrics['success_rate']:.2%} is below 95% threshold.")
        write_halt_signal(STATE_DIR, "Processing success rate too low")
        return False
    
    logger.info("Validation gate passed.")
    return True

def generate_final_report(model_results, evaluation_results):
    """
    Generate the final JSON report with model performance metrics.
    This function fulfills the requirement for T040:
    Output JSON report with mean R², RMSE, MAE for both models.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "model_performance": {},
        "evaluation_results": evaluation_results,
        "status": "complete"
    }

    # Extract metrics from modeling results
    # Expected structure from run_modeling_pipeline:
    # {
    #   "gradient_boosting": {"mean_r2": ..., "mean_rmse": ..., "mean_mae": ...},
    #   "random_forest": {"mean_r2": ..., "mean_rmse": ..., "mean_mae": ...}
    # }
    
    if model_results:
        for model_name, metrics in model_results.items():
            report["model_performance"][model_name] = {
                "mean_r2": metrics.get("mean_r2"),
                "mean_rmse": metrics.get("mean_rmse"),
                "mean_mae": metrics.get("mean_mae")
            }

    # Write report to data/processed/final_report.json
    output_path = DATA_PROCESSED_DIR / "final_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final report written to {output_path}")
    return output_path

def run_pipeline():
    """
    Execute the full pipeline steps in order.
    """
    logger.info("Starting Coating Adhesion Pipeline...")

    # 1. Phase 0: Data Gap Analysis (Check Halt Signal)
    if check_halt_signal():
        logger.critical("Halt signal detected. Aborting pipeline.")
        return 1

    # 2. Phase 1 & 2: Setup & Validation (Implicitly done by directory check)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Phase 3: User Story 1 - Data Ingestion
    # T019-T031 logic
    logger.info("Step 1: Ingesting data...")
    try:
        # Verify sources first (T060, T061, T067 logic)
        # Assuming verify functions are called here or have already run
        # If they failed, a halt signal would be written in T060/T061
        
        # Run ingestion
        processed_df = process_ingestion_data(
            input_dir=str(DATA_RAW_DIR),
            output_dir=str(DATA_PROCESSED_DIR)
        )
        
        if processed_df is None or processed_df.empty:
            logger.error("Ingestion produced no data. Halting.")
            write_halt_signal(STATE_DIR, "Ingestion produced no data")
            return 1
        
        # Save intermediate dataset
        dataset_path = DATA_PROCESSED_DIR / "coating_adhesion_dataset.csv"
        processed_df.to_csv(dataset_path, index=False)
        logger.info(f"Dataset saved to {dataset_path}")

        # T015: Construct Validity Check
        # This function is called within preprocessing_main or here
        # Assuming it writes proxy_validation_report.csv and halts if failed
        # We call the specific check here to ensure it runs before modeling
        validity_check_result = perform_construct_validity_check(str(dataset_path))
        if not validity_check_result.get("passed", False):
            logger.error("Construct validity check failed. Halting.")
            write_halt_signal(STATE_DIR, "Construct validity check failed")
            return 1

    except Exception as e:
        logger.error(f"Ingestion step failed: {e}")
        write_halt_signal(STATE_DIR, f"Ingestion failed: {str(e)}")
        return 1

    # 4. Validation Gate (T028)
    logger.info("Step 2: Running validation gate...")
    metrics = calculate_validation_metrics(str(DATA_RAW_DIR), str(dataset_path))
    if not enforce_validation_gate(metrics):
        logger.critical("Validation gate failed. Halting.")
        return 1

    # 5. Preprocessing (T029, T030)
    logger.info("Step 3: Preprocessing data...")
    try:
        # Encode and standardize
        # These functions are expected to return the processed DataFrame
        # and update the dataset file
        processed_df = encode_compositional_data(processed_df)
        processed_df = standardize_surface_metrics(processed_df)
        
        # Save processed data
        processed_df.to_csv(dataset_path, index=False)
        logger.info("Preprocessing complete.")
    except Exception as e:
        logger.error(f"Preprocessing step failed: {e}")
        write_halt_signal(STATE_DIR, f"Preprocessing failed: {str(e)}")
        return 1

    # 6. User Story 2: Modeling (T034-T039)
    logger.info("Step 4: Training models...")
    model_results = None
    try:
        model_results = run_modeling_pipeline(str(dataset_path))
        
        # T041: Sensitivity Analysis
        logger.info("Running sensitivity analysis for crosslinker proxy...")
        sensitivity_report_path = run_sensitivity_analysis_crosslinker_proxy(str(dataset_path))
        logger.info(f"Sensitivity report saved to {sensitivity_report_path}")
        
    except Exception as e:
        logger.error(f"Modeling step failed: {e}")
        write_halt_signal(STATE_DIR, f"Modeling failed: {str(e)}")
        return 1

    # 7. User Story 3: Evaluation (T045-T049)
    logger.info("Step 5: Evaluating models...")
    evaluation_results = None
    try:
        evaluation_results = run_baseline_evaluation_pipeline(str(dataset_path))
    except Exception as e:
        logger.error(f"Evaluation step failed: {e}")
        # Non-fatal? Or fatal? Plan says it's a comparison, but let's log it.
        # For safety, if the main model worked, we might continue, but the task requires a report.
        # We'll mark it as failed to ensure correctness.
        write_halt_signal(STATE_DIR, f"Evaluation failed: {str(e)}")
        return 1

    # 8. Generate Final Report (T040)
    logger.info("Step 6: Generating final report...")
    try:
        report_path = generate_final_report(model_results, evaluation_results)
        logger.info(f"Pipeline completed successfully. Report: {report_path}")
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}")
        write_halt_signal(STATE_DIR, f"Report generation failed: {str(e)}")
        return 1

    # 9. Update State
    write_state_file(STATE_DIR, "pipeline_complete")

    return 0

def main():
    """Entry point for the script."""
    logger.info("Pipeline execution started.")
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
