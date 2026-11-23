"""
Main orchestrator for the full AM Alloy correlation pipeline (User Story 3).
Executes: Download -> Preprocess -> Train -> Viz -> Report.
Enforces PYTHONHASHSEED=0 for reproducibility.
"""
import os
import sys
import time
import json
import logging
import argparse
import subprocess
from pathlib import Path

# Import configuration
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_results_dir,
    get_models_dir,
    get_figures_dir,
    get_docs_dir,
    get_random_seed,
    get_time_limit_seconds,
    ensure_directories,
    get_logger
)

# Import pipeline components
from data.download import validate_and_download_data
from data.preprocess import validate_and_preprocess
from models.gpr_trainer import train_gpr_model
from models.metrics import evaluate_model, save_metrics
from models.baseline_trainer import train_linear_baseline
from utils.importance_analyzer import run_correlation_analysis
from viz.contour_plots import main as run_contour_plots
from viz.importance import main as run_importance_viz
from viz.uncertainty_metrics import main as run_uncertainty_metrics
from utils.paper_generator import main as run_paper_generator
from utils.logger import log_execution_time, save_runtime_metrics

def setup_pipeline_logging(output_dir: str) -> logging.Logger:
    """Setup logging for the end-to-end pipeline."""
    ensure_directories(output_dir)
    log_file = os.path.join(output_dir, "pipeline.log")
    
    logger = logging.getLogger("e2e_pipeline")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def run_download_step(raw_data_path: str, logger: logging.Logger) -> str:
    """Step 1: Download or validate raw data."""
    logger.info("Starting data download/validation step...")
    start = time.time()
    
    # Ensure raw data directory exists
    raw_dir = get_raw_data_dir()
    ensure_directories(raw_dir)
    
    # Call the download module's main logic
    # We assume validate_and_download_data handles the path logic
    result_path = validate_and_download_data(raw_data_path, logger)
    
    elapsed = time.time() - start
    logger.info(f"Download step completed in {elapsed:.2f}s. Output: {result_path}")
    return result_path

def run_preprocess_step(raw_data_path: str, logger: logging.Logger) -> tuple:
    """Step 2: Preprocess data."""
    logger.info("Starting preprocessing step...")
    start = time.time()
    
    processed_dir = get_processed_data_dir()
    ensure_directories(processed_dir)
    
    # Call preprocessing logic
    train_path, test_path = validate_and_preprocess(raw_data_path, logger)
    
    elapsed = time.time() - start
    logger.info(f"Preprocessing step completed in {elapsed:.2f}s.")
    logger.info(f"Train set: {train_path}, Test set: {test_path}")
    return train_path, test_path

def run_train_step(train_path: str, test_path: str, logger: logging.Logger) -> tuple:
    """Step 3: Train GPR and Baseline models."""
    logger.info("Starting model training step...")
    start = time.time()
    
    models_dir = get_models_dir()
    ensure_directories(models_dir)
    
    # Train GPR
    gpr_model_path = train_gpr_model(train_path, logger)
    
    # Train Baseline
    baseline_model_path = train_linear_baseline(train_path, logger)
    
    # Evaluate
    metrics = evaluate_model(gpr_model_path, baseline_model_path, test_path, logger)
    
    # Save metrics
    metrics_path = os.path.join(get_results_dir(), "metrics.json")
    save_metrics(metrics, metrics_path)
    
    elapsed = time.time() - start
    logger.info(f"Training step completed in {elapsed:.2f}s.")
    return gpr_model_path, baseline_model_path, metrics_path

def run_viz_step(gpr_model_path: str, test_path: str, logger: logging.Logger) -> dict:
    """Step 4: Generate Visualizations."""
    logger.info("Starting visualization step...")
    start = time.time()
    
    figures_dir = get_figures_dir()
    ensure_directories(figures_dir)
    
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    
    # Run Contour Plots
    logger.info("Generating contour plots...")
    run_contour_plots()
    
    # Run Importance Plots
    logger.info("Generating importance plots...")
    run_importance_viz()
    
    # Run Uncertainty Metrics
    logger.info("Calculating uncertainty metrics...")
    run_uncertainty_metrics()
    
    elapsed = time.time() - start
    logger.info(f"Visualization step completed in {elapsed:.2f}s.")
    return {"contour_plots": True, "importance_plots": True, "uncertainty_metrics": True}

def run_report_step(metrics_path: str, logger: logging.Logger) -> str:
    """Step 5: Generate final report/paper."""
    logger.info("Starting report generation step...")
    start = time.time()
    
    docs_dir = get_docs_dir()
    ensure_directories(docs_dir)
    
    # Generate paper
    paper_path = run_paper_generator()
    
    elapsed = time.time() - start
    logger.info(f"Report generation step completed in {elapsed:.2f}s.")
    return paper_path

def run_pipeline(input_path: str, output_dir: str, logger: logging.Logger):
    """Execute the full pipeline."""
    logger.info(f"Starting full pipeline. Input: {input_path}, Output Dir: {output_dir}")
    
    # Ensure output directory exists
    ensure_directories(output_dir)
    
    # 1. Download
    raw_data_path = run_download_step(input_path, logger)
    
    # 2. Preprocess
    train_path, test_path = run_preprocess_step(raw_data_path, logger)
    
    # 3. Train
    gpr_model_path, baseline_model_path, metrics_path = run_train_step(train_path, test_path, logger)
    
    # 4. Viz
    viz_results = run_viz_step(gpr_model_path, test_path, logger)
    
    # 5. Report
    paper_path = run_report_step(metrics_path, logger)
    
    logger.info("Pipeline execution completed successfully.")
    return {
        "raw_data": raw_data_path,
        "train_data": train_path,
        "test_data": test_path,
        "gpr_model": gpr_model_path,
        "baseline_model": baseline_model_path,
        "metrics": metrics_path,
        "viz": viz_results,
        "paper": paper_path
    }

def main():
    parser = argparse.ArgumentParser(description="End-to-End AM Alloy Correlation Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to raw CSV or URL")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for artifacts")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (overrides config)")
    
    args = parser.parse_args()
    
    # Enforce PYTHONHASHSEED=0
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("Warning: PYTHONHASHSEED is not set to 0. Setting it now for reproducibility.")
        os.environ["PYTHONHASHSEED"] = "0"
        # Note: This might require a restart in some environments, but we set it for child processes
    
    # Setup logging
    logger = setup_pipeline_logging(args.output_dir)
    
    # Ensure directories
    ensure_directories(args.output_dir)
    
    start_time = time.time()
    
    try:
        results = run_pipeline(args.input, args.output_dir, logger)
        
        # Save runtime
        total_time = time.time() - start_time
        metrics_path = os.path.join(args.output_dir, "metrics.json")
        
        # Load existing metrics if present, else create new
        metrics_data = {}
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics_data = json.load(f)
        
        metrics_data["total_runtime_seconds"] = total_time
        metrics_data["feasibility_status"] = "SUCCESS"
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Total runtime: {total_time:.2f}s")
        logger.info(f"Results saved to {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        # Save failure status
        metrics_path = os.path.join(args.output_dir, "metrics.json")
        metrics_data = {"total_runtime_seconds": time.time() - start_time, "feasibility_status": "FAILED", "error": str(e)}
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
