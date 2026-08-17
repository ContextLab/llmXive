import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

from config import ensure_dirs, DataConfig, TrainingConfig, AnalysisConfig
from utils.logger import get_logger

# Import all stage modules
from data.schema_check import main as schema_check_main
from data.download import main as download_main
from data.mapping import main as mapping_main
from data.clean import main as clean_main
from data.descriptors import main as descriptors_main
from data.exclusion_report import main as exclusion_report_main
from data.finalize_dataset import main as finalize_dataset_main
from data.split import main as split_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.save_artifacts import main as save_artifacts_main
from analysis.collinearity import main as collinearity_main
from analysis.interpret import main as interpret_main
from analysis.sensitivity_runner import main as sensitivity_runner_main
from analysis.hyperparameter_sensitivity import main as hyperparameter_sensitivity_main
from analysis.consistency import main as consistency_main
from analysis.final_report import main as final_report_main

def setup_logging_pipeline(log_dir: Path):
    """Setup logging for the full pipeline."""
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger("pipeline")

def run_stage(stage_name: str, stage_func, logger: logging.Logger) -> bool:
    """Run a single stage of the pipeline."""
    logger.info(f"Starting stage: {stage_name}")
    start_time = time.time()
    try:
        result = stage_func()
        elapsed = time.time() - start_time
        if result == 0:
            logger.info(f"Stage {stage_name} completed successfully in {elapsed:.2f}s")
            return True
        else:
            logger.error(f"Stage {stage_name} failed with return code {result}")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Stage {stage_name} failed with exception: {e} (took {elapsed:.2f}s)", exc_info=True)
        return False

def run_full_pipeline(logger: logging.Logger, config: DataConfig) -> bool:
    """Run the full pipeline from ingestion to final report."""
    stages = [
        ("Schema Check", schema_check_main),
        ("Download Data", download_main),
        ("Map Columns", mapping_main),
        ("Clean and Filter", clean_main),
        ("Compute Descriptors", descriptors_main),
        ("Generate Exclusion Report", exclusion_report_main),
        ("Finalize Dataset", finalize_dataset_main),
        ("Split Dataset", split_main),
        ("Train Model", train_main),
        ("Evaluate Model", evaluate_main),
        ("Save Artifacts", save_artifacts_main),
        ("Collinearity Analysis", collinearity_main),
        ("Interpretability Analysis", interpret_main),
        ("Sensitivity Analysis", sensitivity_runner_main),
        ("Hyperparameter Sensitivity", hyperparameter_sensitivity_main),
        ("Consistency Analysis", consistency_main),
        ("Generate Final Report", final_report_main),
    ]
    
    all_passed = True
    for stage_name, stage_func in stages:
        if not run_stage(stage_name, stage_func, logger):
            logger.error(f"Pipeline failed at stage: {stage_name}")
            all_passed = False
            # Continue running remaining stages to collect as much data as possible
            # but mark the pipeline as failed
    
    return all_passed

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run the full SN1 rate constant prediction pipeline")
    parser.add_argument("--log-dir", type=str, default="artifacts/logs",
                      help="Directory for log files")
    parser.add_argument("--config", type=str, default="config.yaml",
                      help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_dirs(DataConfig())
    ensure_dirs(TrainingConfig())
    ensure_dirs(AnalysisConfig())
    
    # Setup logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging_pipeline(log_dir)
    
    logger.info("Starting SN1 Rate Constant Prediction Pipeline")
    start_time = time.time()
    
    # Run the full pipeline
    success = run_full_pipeline(logger, DataConfig())
    
    elapsed_time = time.time() - start_time
    
    # Log final status
    if success:
        logger.info(f"Pipeline completed successfully in {elapsed_time:.2f}s")
    else:
        logger.error(f"Pipeline completed with errors in {elapsed_time:.2f}s")
    
    # Save feasibility test log
    feasibility_log = {
        "start_time": datetime.now().isoformat(),
        "elapsed_seconds": elapsed_time,
        "status": "success" if success else "failed",
        "config": args.config
    }
    
    feasibility_log_path = Path("artifacts/feasibility_test_log.json")
    feasibility_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(feasibility_log_path, 'w', encoding='utf-8') as f:
        json.dump(feasibility_log, f, indent=2)
    
    logger.info(f"Feasibility test log saved to {feasibility_log_path}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
