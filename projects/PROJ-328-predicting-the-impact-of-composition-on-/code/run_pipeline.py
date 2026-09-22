"""
T060: Reconcile run-book vs implementation.
This script acts as the main entry point for the pipeline execution,
ensuring all required steps (Ingestion, Features, Models, Evaluation, Reporting)
are run in the correct order and that declared deliverables are produced.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from config import get_data_processed_dir

logger = get_logger(__name__)

def run_step(step_name: str, module_path: str, func_name: str = "main"):
    """
    Dynamically import and run a specific function from a module.
    """
    logger.info(f"--- Running Step: {step_name} ---")
    try:
        # Construct module path relative to code/
        # e.g., "ingestion.cleaner"
        full_module_name = f"code.{module_path}"
        
        # Import the module
        mod = __import__(full_module_name, fromlist=[func_name])
        
        # Get the function
        if not hasattr(mod, func_name):
            raise AttributeError(f"Module {full_module_name} has no attribute '{func_name}'")
        
        func = getattr(mod, func_name)
        
        # Run the function
        func()
        
        logger.info(f"--- Step {step_name} completed successfully ---")
        return True
    except Exception as e:
        logger.error(f"--- Step {step_name} FAILED: {e} ---", exc_info=True)
        return False

def verify_deliverables():
    """
    Verify that critical deliverables exist after pipeline run.
    """
    processed_dir = get_data_processed_dir()
    required_files = [
        processed_dir / "solder_hardness_cleaned.csv",
        processed_dir / ".ingestion_status.json",
        processed_dir / "report.yaml",
        processed_dir / "test_metrics.yaml"
    ]
    
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f))
    
    if missing:
        logger.warning(f"Missing critical deliverables: {missing}")
        # Do not exit with error here, as the pipeline might have partial success
        # but we log it for the user.
    else:
        logger.info("All critical deliverables verified.")

def main():
    """
    Execute the full pipeline.
    """
    logger.info("Starting full pipeline execution.")
    
    # 1. Ingestion (T012, T013, T014)
    # Note: T012a (API) and T012d (Scraper) are usually run separately or via aggregator.
    # We assume raw data exists or the aggregator handles fetching if configured.
    # For this run, we focus on cleaning and validation which are the core data prep steps.
    steps = [
        ("Data Cleaning & Validation", "ingestion.cleaner"),
        ("Data Validation & Status", "ingestion.validator"),
        ("Generate Validation Report", "ingestion.generate_validation_report"),
        
        # 2. Features (T023)
        ("CLR Transformation", "features.transformer"),
        ("Descriptor Engineering", "features.descriptor_engine"),
        ("Collinearity Check", "features.collinearity"),
        
        # 3. Models (T025, T026)
        ("XGBoost Training", "models.xgboost_trainer"),
        ("Linear Regression Training", "models.linear_trainer"),
        
        # 4. Evaluation (T027, T029, T030, T031)
        ("Cross Validation", "evaluation.cv"),
        ("Bootstrap Metrics", "evaluation.bootstrap"),
        ("SHAP Analysis", "evaluation.shap_analysis"),
        ("Model Comparison", "evaluation.model_comparison"),
        ("Generate Predictions & Metrics", "evaluation.predict"),
        ("Generate Report YAML", "evaluation.generate_report"),
        
        # 5. Reporting & Warnings (T035, T056, T057)
        ("Add Power Limitation Warning", "evaluation.add_power_limitation_warning"),
    ]
    
    success = True
    for step_name, module in steps:
        if not run_step(step_name, module):
            logger.error(f"Pipeline halted at step: {step_name}")
            success = False
            break
    
    if success:
        verify_deliverables()
        logger.info("Pipeline execution completed.")
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()