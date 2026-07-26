"""
Benchmark script to verify the pipeline completes within 6 hours on a CPU-only runner.

This script orchestrates the full pipeline execution and measures the wall-clock time.
It invokes the main entry points of each stage in the correct dependency order:
1. Data Ingestion (T016)
2. Cleaning (T017)
3. Feature Engineering (T018, T019)
4. Target Validation (T021)
5. Data Splitting (T020)
6. Model Training (T025, T026)
7. Model Evaluation (T027, T028, T030)
8. Report Generation (T029)
9. Feature Importance (T034, T035)
10. Visualization (T037, T038)

Time Limit: 6 hours (21,600 seconds)
"""
import os
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_paths, ensure_directories, set_random_seed
from utils.logging_config import configure_root_logger
from utils.provenance import ensure_state_directory, get_provenance_state_file, record_artifact

# Import pipeline stages
from data.ingest import main as ingest_main
from data.clean import main as clean_main
from data.features import main as features_main
from data.validate_target import main as validate_main
from data.split import main as split_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.generate_report import main as report_main
from models.importance import main as importance_main
from viz.plots import main as viz_main
from viz.save_visualizations import main as save_viz_main

logger = logging.getLogger(__name__)

# Configuration
TIME_LIMIT_SECONDS = 6 * 60 * 60  # 6 hours
PROJECT_ID = "PROJ-380-predicting-the-impact-of-composition-on-"

def run_stage(stage_name, stage_func, args=None):
    """Execute a pipeline stage and measure its duration."""
    logger.info(f"--- Starting Stage: {stage_name} ---")
    start_time = time.time()
    
    try:
        # Prepare arguments for the stage
        stage_args = []
        if args:
            stage_args = args
        
        # Execute the stage
        stage_func(*stage_args)
        
        duration = time.time() - start_time
        logger.info(f"--- Completed Stage: {stage_name} in {duration:.2f} seconds ---")
        return True, duration
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"--- Failed Stage: {stage_name} after {duration:.2f} seconds ---")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False, duration

def main():
    parser = argparse.ArgumentParser(description="Benchmark pipeline execution time")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--limit", type=int, default=TIME_LIMIT_SECONDS, help="Time limit in seconds")
    args = parser.parse_args()

    # Setup
    set_random_seed(args.seed)
    configure_root_logger(level=logging.INFO)
    paths = get_paths()
    ensure_directories(paths)
    ensure_state_directory(paths)
    
    logger.info(f"Starting pipeline benchmark with time limit: {args.limit} seconds")
    logger.info(f"Project ID: {PROJECT_ID}")
    
    total_start = time.time()
    stage_times = {}
    all_success = True

    # 1. Data Ingestion
    success, duration = run_stage("Ingestion", ingest_main)
    stage_times["ingestion"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at ingestion stage")
        return False

    # 2. Cleaning
    success, duration = run_stage("Cleaning", clean_main)
    stage_times["cleaning"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at cleaning stage")
        return False

    # 3. Feature Engineering
    success, duration = run_stage("Feature Engineering", features_main)
    stage_times["features"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at feature engineering stage")
        return False

    # 4. Target Validation
    success, duration = run_stage("Target Validation", validate_main)
    stage_times["validation"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at target validation stage")
        return False

    # 5. Data Splitting
    success, duration = run_stage("Data Splitting", split_main)
    stage_times["splitting"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at data splitting stage")
        return False

    # 6. Model Training
    success, duration = run_stage("Model Training", train_main)
    stage_times["training"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at model training stage")
        return False

    # 7. Model Evaluation
    success, duration = run_stage("Model Evaluation", evaluate_main)
    stage_times["evaluation"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at model evaluation stage")
        return False

    # 8. Report Generation
    success, duration = run_stage("Report Generation", report_main)
    stage_times["report_generation"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at report generation stage")
        return False

    # 9. Feature Importance
    success, duration = run_stage("Feature Importance", importance_main)
    stage_times["importance"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at feature importance stage")
        return False

    # 10. Visualization (Plots)
    success, duration = run_stage("Visualization", viz_main)
    stage_times["visualization"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at visualization stage")
        return False

    # 11. Save Visualizations
    success, duration = run_stage("Save Visualizations", save_viz_main)
    stage_times["save_visualizations"] = duration
    if not success:
        all_success = False
        logger.error("Pipeline failed at save visualizations stage")
        return False

    total_duration = time.time() - total_start

    # Summary
    logger.info("=" * 60)
    logger.info("PIPELINE BENCHMARK SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Execution Time: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    logger.info(f"Time Limit: {args.limit} seconds ({args.limit/3600:.2f} hours)")
    logger.info(f"Status: {'PASS' if total_duration <= args.limit else 'FAIL'}")
    logger.info("-" * 60)
    logger.info("Stage Breakdown:")
    for stage, duration in stage_times.items():
        logger.info(f"  {stage}: {duration:.2f} seconds")
    logger.info("=" * 60)

    # Record provenance
    try:
        state_file = get_provenance_state_file(paths)
        record_artifact(
            state_file,
            "benchmark_results",
            {
                "total_time_seconds": total_duration,
                "time_limit_seconds": args.limit,
                "passed": total_duration <= args.limit,
                "stage_times": stage_times,
                "timestamp": datetime.now().isoformat(),
                "seed": args.seed
            }
        )
        logger.info(f"Benchmark results recorded to {state_file}")
    except Exception as e:
        logger.warning(f"Failed to record provenance: {e}")

    if total_duration > args.limit:
        logger.error(f"Pipeline exceeded time limit of {args.limit} seconds by {total_duration - args.limit:.2f} seconds")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
