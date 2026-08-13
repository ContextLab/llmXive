import sys
import time
import json
import logging
from pathlib import Path
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_results_dir,
    get_models_dir,
    get_figures_dir,
    get_docs_dir,
    get_state_dir,
    get_logs_dir,
    get_random_seed,
    get_time_limit_seconds,
    ensure_directories,
    get_logger
)
from data.preprocess import validate_and_preprocess
from models.gpr_trainer import main as train_gpr_main
from models.baseline_trainer import main as train_baseline_main
from models.metrics import main as save_metrics_main
from viz.contour_plots import main as viz_contour_main
from viz.importance import main as viz_importance_main
from utils.logger import log_execution_time, save_runtime_metrics

def run_pipeline():
    """
    Orchestrates the full research pipeline:
    1. Data Preprocessing (US1)
    2. Model Training (US2)
    3. Visualization (US3)
    4. Runtime Validation (SC-005)
    """
    logger = get_logger("pipeline")
    start_time = time.time()
    
    logger.info("Starting research pipeline...")
    
    # 1. Preprocessing
    logger.info("Step 1: Preprocessing data...")
    validate_and_preprocess()
    
    # 2. Model Training
    logger.info("Step 2: Training GPR and Baseline models...")
    train_gpr_main()
    train_baseline_main()
    
    # 3. Evaluation & Metrics
    logger.info("Step 3: Evaluating models and saving metrics...")
    save_metrics_main()
    
    # 4. Visualization
    logger.info("Step 4: Generating visualizations...")
    viz_contour_main()
    viz_importance_main()
    
    # 5. Runtime Validation (T048 / SC-005)
    end_time = time.time()
    total_runtime_seconds = end_time - start_time
    
    time_limit_seconds = get_time_limit_seconds()
    
    logger.info(f"Total runtime: {total_runtime_seconds:.2f} seconds")
    logger.info(f"Time limit: {time_limit_seconds} seconds")
    
    # Explicitly log the result of the runtime measurement against the limit
    if total_runtime_seconds < time_limit_seconds:
        logger.info("PASS: Runtime within 6-hour limit")
        runtime_status = "PASS"
    else:
        logger.error("FAIL: Runtime exceeds limit")
        runtime_status = "FAIL"
    
    # Save runtime metrics to results/metrics.json
    save_runtime_metrics({
        "total_runtime_seconds": total_runtime_seconds,
        "time_limit_seconds": time_limit_seconds,
        "status": runtime_status
    })
    
    logger.info("Pipeline execution completed.")
    return 0

if __name__ == "__main__":
    sys.exit(run_pipeline())