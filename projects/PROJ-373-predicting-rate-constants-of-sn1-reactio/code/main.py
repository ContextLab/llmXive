"""
Main orchestration script for the SN1 Rate Constant Prediction Pipeline.

This script coordinates the execution of the full pipeline:
1. Data Ingestion (T011)
2. Data Cleaning (T012)
3. Descriptor Calculation (T013)
4. Data Splitting (T014)
5. Exclusion Report Generation (T015)
6. Dataset Finalization (T016)
7. Model Training (T020)
8. Model Evaluation (T021)
9. Model Artifact Saving (T022)
10. Interpretability Analysis (T026, T029)
11. Sensitivity Analysis (T027)
12. Collinearity Analysis (T028)
13. Power Analysis (T035)
14. Report Generation (T030)

Usage:
    python code/main.py [--skip-data] [--skip-model] [--skip-analysis]
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from utils.checksum import compute_file_checksum

# Import pipeline stages
from data.ingest import main as ingest_main
from data.clean import main as clean_main
from data.descriptors import main as descriptors_main
from data.split import main as split_main
from data.exclusion_report import main as exclusion_report_main
from data.finalize_dataset import main as finalize_dataset_main

from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.save_artifacts import main as save_artifacts_main

from analysis.interpret import main as interpret_main
from analysis.sensitivity import main as sensitivity_main
from analysis.collinearity import main as collinearity_main
from analysis.power import main as power_main
from analysis.generate_reports import main as generate_reports_main

logger = get_logger(__name__)

def run_stage(stage_name, stage_func, args=None):
    """
    Execute a pipeline stage with error handling and logging.
    
    Args:
        stage_name: Human-readable name of the stage
        stage_func: Function to execute (expects main() signature)
        args: Optional arguments to pass to the stage function
    """
    logger.info(f"--- Starting Stage: {stage_name} ---")
    try:
        if args:
            stage_func(args)
        else:
            stage_func()
        logger.info(f"--- Completed Stage: {stage_name} ---")
        return True
    except Exception as e:
        logger.error(f"--- Failed Stage: {stage_name} ---")
        logger.error(f"Error: {str(e)}")
        raise

def main():
    """
    Main orchestration entry point.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate the SN1 Rate Constant Prediction Pipeline"
    )
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip data ingestion, cleaning, and preprocessing stages"
    )
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Skip model training and evaluation stages"
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis and reporting stages"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger.info("Starting SN1 Rate Constant Prediction Pipeline")
    
    # Ensure directories exist
    ensure_dirs()
    
    success = True
    
    # Stage 1: Data Ingestion and Preprocessing
    if not args.skip_data:
        logger.info("Executing Data Pipeline...")
        
        try:
            # T011: Ingest data
            run_stage("Data Ingestion", ingest_main)
            
            # T012: Clean data
            run_stage("Data Cleaning", clean_main)
            
            # T013: Compute descriptors
            run_stage("Descriptor Calculation", descriptors_main)
            
            # T014: Split data
            run_stage("Data Splitting", split_main)
            
            # T015: Generate exclusion report
            run_stage("Exclusion Report", exclusion_report_main)
            
            # T016: Finalize dataset
            run_stage("Dataset Finalization", finalize_dataset_main)
            
            logger.info("Data Pipeline completed successfully.")
            
        except Exception as e:
            logger.error(f"Data Pipeline failed: {str(e)}")
            success = False
            if not args.skip_model:
                logger.warning("Skipping model stages due to data pipeline failure")
                args.skip_model = True
            if not args.skip_analysis:
                logger.warning("Skipping analysis stages due to data pipeline failure")
                args.skip_analysis = True
    
    # Stage 2: Model Training and Evaluation
    if not args.skip_model and success:
        logger.info("Executing Model Pipeline...")
        
        try:
            # T020: Train model with hyperparameter optimization
            run_stage("Model Training", train_main)
            
            # T021: Evaluate model
            run_stage("Model Evaluation", evaluate_main)
            
            # T022: Save artifacts
            run_stage("Artifact Saving", save_artifacts_main)
            
            logger.info("Model Pipeline completed successfully.")
            
        except Exception as e:
            logger.error(f"Model Pipeline failed: {str(e)}")
            success = False
            if not args.skip_analysis:
                logger.warning("Skipping analysis stages due to model pipeline failure")
                args.skip_analysis = True
    
    # Stage 3: Analysis and Reporting
    if not args.skip_analysis and success:
        logger.info("Executing Analysis Pipeline...")
        
        try:
            # T026, T029: Interpretability
            run_stage("Interpretability Analysis", interpret_main)
            
            # T027: Sensitivity analysis
            run_stage("Sensitivity Analysis", sensitivity_main)
            
            # T028: Collinearity analysis
            run_stage("Collinearity Analysis", collinearity_main)
            
            # T035: Power analysis
            run_stage("Power Analysis", power_main)
            
            # T030: Generate reports
            run_stage("Report Generation", generate_reports_main)
            
            logger.info("Analysis Pipeline completed successfully.")
            
        except Exception as e:
            logger.error(f"Analysis Pipeline failed: {str(e)}")
            success = False
    
    # Final summary
    if success:
        logger.info("=" * 50)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 50)
        logger.info("Output artifacts:")
        logger.info("  - data/processed/cleaned_sn1.csv")
        logger.info("  - artifacts/best_model.pt")
        logger.info("  - artifacts/metrics.json")
        logger.info("  - artifacts/feature_importance.png")
        logger.info("  - artifacts/sensitivity_report.csv")
        logger.info("  - artifacts/perturbation_results.csv")
        logger.info("  - artifacts/power_analysis_report.csv")
    else:
        logger.warning("=" * 50)
        logger.warning("Pipeline completed with errors.")
        logger.warning("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())