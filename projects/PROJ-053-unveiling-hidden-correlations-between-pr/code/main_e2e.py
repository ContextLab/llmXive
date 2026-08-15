"""
End-to-End Pipeline Orchestrator for PROJ-053
Orchestrates: Download -> Preprocess -> Train -> Viz -> Report
"""
import os
import sys
import time
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    ensure_directories,
    get_logger,
    get_time_limit_seconds
)
from data.preprocess import validate_and_preprocess, main as preprocess_main
from data.schema_validator import validate_and_report, main as validator_main
from models.gpr_trainer import train_gpr_model, main as gpr_main
from models.metrics import save_metrics, main as metrics_main
from models.saver import save_models
from viz.contour_plots import main as contour_main
from viz.importance import main as importance_main
from viz.uncertainty_metrics import main as uncertainty_main
from utils.logger import save_runtime_metrics, log_execution_time
from utils.runtime_verifier import verify_runtime_limit

def setup_pipeline_logging():
    """Configure logging for the end-to-end pipeline."""
    ensure_directories()
    logger = get_logger("e2e_pipeline")
    return logger

def run_download_step(logger):
    """
    Execute data download step.
    Note: T014A handles download logic. We assume data/raw/am_data.csv exists
    or is placed manually as per instructions.
    """
    logger.info("Starting Data Download/Verification step...")
    raw_dir = get_raw_data_dir()
    raw_file = os.path.join(raw_dir, "am_data.csv")
    
    if not os.path.exists(raw_file):
        logger.warning(f"Raw data file not found at {raw_file}. "
                     "Expected manual placement or previous download step.")
        # In a strict e2e run, we might fail here, but per T043 notes,
        # we assume the pipeline can proceed if data exists.
        # For this implementation, we assume the file exists or T014A was run.
        # If it truly doesn't exist, the preprocess step will fail loudly.
    else:
        logger.info(f"Raw data found at {raw_file}")
    
    return raw_file

def run_preprocess_step(logger, raw_file):
    """
    Execute data preprocessing: validation, imputation, encoding, scaling.
    """
    logger.info("Starting Data Preprocessing step...")
    # The validate_and_preprocess function handles the full pipeline from raw to processed
    try:
        # Call the main entry point of the preprocess module
        # This function is expected to handle schema validation, imputation, etc.
        preprocess_main() 
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise

def run_train_step(logger):
    """
    Execute model training: GPR and Baseline.
    """
    logger.info("Starting Model Training step...")
    try:
        # Train GPR and Baseline models
        gpr_main()
        logger.info("Model training completed successfully.")
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise

def run_viz_step(logger):
    """
    Execute visualization step: Contour plots, Uncertainty heatmaps, PDPs.
    """
    logger.info("Starting Visualization step...")
    try:
        # Generate Contour Plots
        contour_main()
        
        # Generate Importance/PDP Plots
        importance_main()
        
        # Calculate and Save Uncertainty Metrics
        uncertainty_main()
        
        logger.info("Visualization step completed successfully.")
    except Exception as e:
        logger.error(f"Visualization step failed: {str(e)}")
        raise

def run_report_step(logger):
    """
    Compile final report and metrics.
    """
    logger.info("Starting Report Compilation step...")
    try:
        # Ensure all metrics are saved to results/metrics.json
        # This is typically handled by metrics_main and save_runtime_metrics
        # but we call it here to ensure final aggregation
        metrics_main()
        
        # Save final runtime metrics
        save_runtime_metrics()
        
        logger.info("Report compilation completed successfully.")
    except Exception as e:
        logger.error(f"Report compilation failed: {str(e)}")
        raise

def run_pipeline():
    """
    Main entry point for the End-to-End Pipeline.
    Executes steps sequentially: Download -> Preprocess -> Train -> Viz -> Report
    """
    start_time = time.time()
    logger = setup_pipeline_logging()
    
    logger.info("=" * 60)
    logger.info("Starting PROJ-053 End-to-End Pipeline")
    logger.info("=" * 60)
    
    try:
        # Step 1: Download/Verify Data
        raw_file = run_download_step(logger)
        
        # Step 2: Preprocess Data
        run_preprocess_step(logger, raw_file)
        
        # Step 3: Train Models
        run_train_step(logger)
        
        # Step 4: Generate Visualizations
        run_viz_step(logger)
        
        # Step 5: Compile Report
        run_report_step(logger)
        
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.info("=" * 60)
        logger.info(f"Pipeline completed successfully in {total_runtime:.2f} seconds")
        logger.info("=" * 60)
        
        # Verify runtime limit
        verify_runtime_limit(total_runtime)
        
        return True
        
    except Exception as e:
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.error("=" * 60)
        logger.error(f"Pipeline failed after {total_runtime:.2f} seconds: {str(e)}")
        logger.error("=" * 60)
        
        # Still save runtime metrics even on failure
        try:
            save_runtime_metrics()
        except Exception as save_err:
            logger.error(f"Failed to save runtime metrics on error: {str(save_err)}")
        
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)