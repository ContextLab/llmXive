"""
Main entry point for the Heusler Alloy Hysteresis Prediction Pipeline.
Orchestrates ingestion, preprocessing, feature engineering, modeling, and reporting.
"""
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path if not already present
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging, create_logger
from src.ingestion.ingest_pipeline import main as run_ingestion
from src.preprocessing.preprocess_pipeline import main as run_preprocessing
from src.features.feature_engineering_pipeline import main as run_feature_engineering
from src.models.training_pipeline import main as run_model_training
from src.validation.final_evaluator import main as run_final_evaluation
from src.preprocessing.scarcity_checker import main as run_scarcity_check
from src.preprocessing.completeness_reporter import main as run_completeness_report
from src.validation.bootstrap_validation import main as run_bootstrap_validation
from src.validation.pdp_generator import main as run_pdp_generation
from src.validation.stratified_reporter import main as run_stratified_report
from src.validation.outlier_detection import main as run_outlier_detection

def main():
    """
    Execute the full pipeline end-to-end.
    """
    start_time = datetime.now()
    logger = create_logger("main")
    logger.info("="*60)
    logger.info("Starting Heusler Alloy Hysteresis Prediction Pipeline")
    logger.info("="*60)

    try:
        # 1. Ingestion (Fetch and merge raw data)
        logger.info("Step 1/10: Running Ingestion Pipeline...")
        run_ingestion()

        # 2. Preprocessing (Standardize, filter, impute)
        logger.info("Step 2/10: Running Preprocessing Pipeline...")
        run_preprocessing()

        # 3. Scarcity Check (Check N and warn)
        logger.info("Step 3/10: Running Scarcity Check...")
        run_scarcity_check()

        # 4. Completeness Report
        logger.info("Step 4/10: Generating Completeness Report...")
        run_completeness_report()

        # 5. Feature Engineering
        logger.info("Step 5/10: Running Feature Engineering Pipeline...")
        run_feature_engineering()

        # 6. Model Training
        logger.info("Step 6/10: Running Model Training Pipeline...")
        run_model_training()

        # 7. Outlier Detection & Sensitivity
        logger.info("Step 7/10: Running Outlier Detection...")
        run_outlier_detection()

        # 8. Bootstrap Validation
        logger.info("Step 8/10: Running Bootstrap Validation...")
        run_bootstrap_validation()

        # 9. PDP Generation
        logger.info("Step 9/10: Generating Partial Dependence Plots...")
        run_pdp_generation()

        # 10. Stratified Analysis & Final Report
        logger.info("Step 10/10: Running Stratified Analysis and Final Evaluation...")
        run_stratified_report()
        run_final_evaluation()

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info("="*60)
        logger.info(f"Pipeline completed successfully in {duration}")
        logger.info("="*60)

    except FileNotFoundError as e:
        logger.error(f"Critical Error: Missing required file or directory. {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    main()
