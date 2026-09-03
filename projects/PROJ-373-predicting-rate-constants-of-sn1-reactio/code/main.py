"""
Main orchestration script for the SN1 Rate Constant Prediction Pipeline.
Executes the full pipeline from data ingestion to final report generation.
"""
import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, TrainingConfig, AnalysisConfig, ensure_dirs
from utils.logger import get_logger

# Import pipeline stages
# Data Pipeline
from data.schema_check import main as schema_check_main
from data.download import main as download_main
from data.mapping import main as mapping_main
from data.clean import main as clean_main
from data.descriptors import main as descriptors_main
from data.exclusion_report import main as exclusion_report_main
from data.finalize_dataset import main as finalize_dataset_main
from data.split import main as split_main

# Models
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.save_artifacts import main as save_artifacts_main

# Analysis
from analysis.collinearity import main as collinearity_main
from analysis.sensitivity_runner import main as sensitivity_runner_main
from analysis.hyperparameter_sensitivity import main as hyperparameter_sensitivity_main
from analysis.consistency import main as consistency_main
from analysis.interpret import main as interpret_main
from analysis.final_report import main as final_report_main
from data.final_validation import main as final_validation_main

def setup_logging_pipeline(log_dir: Path):
    """Setup logging for the pipeline."""
    ensure_dirs()
    log_file = log_dir / "pipeline_run.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger(__name__)

def run_stage(name: str, func, *args, **kwargs):
    """Run a pipeline stage with timing and error handling."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting stage: {name}")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"Stage {name} completed successfully in {elapsed:.2f}s")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Stage {name} failed after {elapsed:.2f}s: {str(e)}")
        raise

def run_full_pipeline():
    """Execute the full SN1 rate constant prediction pipeline."""
    config = DataConfig()
    ensure_dirs()
    logger = setup_logging_pipeline(Path(config.log_dir))

    logger.info("="*60)
    logger.info("Starting Full SN1 Rate Constant Prediction Pipeline")
    logger.info("="*60)

    start_time = time.time()

    # --- Data Ingestion and Preprocessing ---
    logger.info("Phase 1: Data Ingestion and Preprocessing")

    # T011a: Schema Check
    run_stage("Schema Check", schema_check_main)

    # T011b: Download
    run_stage("Download", download_main)

    # T011c: Mapping
    run_stage("Mapping", mapping_main)

    # T012: Clean and Filter
    run_stage("Clean and Filter", clean_main)

    # T013: Descriptors
    run_stage("Descriptors", descriptors_main)

    # T015: Exclusion Report
    run_stage("Exclusion Report", exclusion_report_main)

    # T016: Finalize Dataset
    run_stage("Finalize Dataset", finalize_dataset_main)

    # T014: Split
    run_stage("Split", split_main)

    # --- Model Training and Evaluation ---
    logger.info("Phase 2: Model Training and Evaluation")

    # T019-T022: Training
    run_stage("Train MPNN", train_main)

    # T021-T022: Evaluation and Save Artifacts
    run_stage("Evaluate", evaluate_main)
    run_stage("Save Artifacts", save_artifacts_main)

    # --- Analysis and Interpretability ---
    logger.info("Phase 3: Analysis and Interpretability")

    # T028: Collinearity
    run_stage("Collinearity Analysis", collinearity_main)

    # T036: Sensitivity Runner
    run_stage("Sensitivity Analysis", sensitivity_runner_main)

    # T037: Hyperparameter Sensitivity
    run_stage("Hyperparameter Sensitivity", hyperparameter_sensitivity_main)

    # T035: Consistency
    run_stage("Consistency Analysis", consistency_main)

    # T026-T029: Interpretability
    run_stage("Interpretability", interpret_main)

    # --- Final Validation and Reporting ---
    logger.info("Phase 4: Final Validation and Reporting")

    # T040: Final Validation (this stage)
    run_stage("Final Validation", final_validation_main)

    # T039: Final Report
    run_stage("Generate Final Report", final_report_main)

    total_time = time.time() - start_time
    logger.info("="*60)
    logger.info(f"Pipeline completed successfully in {total_time:.2f}s")
    logger.info("="*60)

    # Log feasibility metrics
    feasibility_log = {
        "total_runtime_seconds": total_time,
        "status": "success",
        "artifacts_generated": [
            "data/processed/cleaned_sn1.csv",
            "data/processed/exclusion_report.csv",
            "artifacts/best_model.pt",
            "artifacts/metrics.json",
            "artifacts/final_report.md"
        ]
    }

    with open(Path(config.artifacts_dir) / "feasibility_test_log.json", 'w') as f:
        json.dump(feasibility_log, f, indent=2)

    return True

def main():
    parser = argparse.ArgumentParser(description="SN1 Rate Constant Prediction Pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--stage", type=str, help="Run specific stage")
    args = parser.parse_args()

    if args.full or not args.stage:
        run_full_pipeline()
    else:
        # Placeholder for single stage execution if needed
        logging.error("Single stage execution not fully implemented in this task.")
        sys.exit(1)

if __name__ == "__main__":
    main()
