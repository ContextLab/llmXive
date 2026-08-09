"""
Main entry point for the Heusler Alloy Hysteresis Prediction Pipeline.
Orchestrates the full execution flow from ingestion to final report generation.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add code/src to path if running as script
if __name__ == "__main__":
    code_root = Path(__file__).parent
    if str(code_root / "src") not in sys.path:
        sys.path.insert(0, str(code_root))
    if str(code_root / "scripts") not in sys.path:
        sys.path.insert(0, str(code_root))

from src.utils.logging_config import setup_logging, create_logger
from src.ingestion.ingest_pipeline import main as run_ingestion
from src.preprocessing.preprocess_pipeline import main as run_preprocessing
from src.preprocessing.scarcity_checker import main as run_scarcity_check
from src.features.feature_engineering_pipeline import main as run_feature_engineering
from src.models.training_pipeline import main as run_training
from src.models.feature_importance import main as run_feature_importance
from src.validation.null_model_comparison import main as run_null_comparison
from src.validation.bootstrap_validation import main as run_bootstrap_validation
from src.validation.pdp_generator import main as run_pdp_generation
from src.validation.stratified_analysis import main as run_stratified_analysis
from src.validation.stratified_reporter import main as run_stratified_reporter
from src.validation.final_evaluator import main as run_final_evaluator
from src.preprocessing.completeness_reporter import main as run_completeness_report
from src.preprocessing.fr001_gate import main as run_fr001_gate
from src.validation.scarcity_warning import main as run_scarcity_warning_report
from src.validation.microstructure_confounding_analysis import main as run_microstructure_analysis
from src.features.descriptor_robustness import main as run_descriptor_robustness
from src.validation.confounder_quantification import main as run_confounder_quantification

def main():
    """Execute the full research pipeline."""
    logger = setup_logging("pipeline_execution", level=logging.INFO)
    logger.info("Starting Heusler Alloy Hysteresis Prediction Pipeline")
    logger.info(f"Start Time: {datetime.now().isoformat()}")

    try:
        # Phase 1: Ingestion
        logger.info(">>> Phase 1: Data Ingestion")
        run_ingestion()

        # Phase 2: Preprocessing
        logger.info(">>> Phase 2: Data Preprocessing")
        run_preprocessing()

        # Phase 3: Scarcity Check & FR-001 Gate
        logger.info(">>> Phase 3: Scarcity Check & Validation Gates")
        run_fr001_gate()
        run_scarcity_check()
        run_completeness_report()
        run_scarcity_warning_report()

        # Phase 4: Feature Engineering
        logger.info(">>> Phase 4: Feature Engineering")
        run_feature_engineering()

        # Phase 5: Model Training
        logger.info(">>> Phase 5: Model Training")
        run_training()
        run_feature_importance()

        # Phase 6: Statistical Validation
        logger.info(">>> Phase 6: Statistical Validation")
        run_null_comparison()
        run_bootstrap_validation()
        run_pdp_generation()
        run_stratified_analysis()
        run_stratified_reporter()
        run_confounder_quantification()

        # Phase 7: Robustness & Final Reporting
        logger.info(">>> Phase 7: Robustness Checks & Final Report")
        run_descriptor_robustness()
        run_microstructure_analysis()
        run_final_evaluator()

        logger.info("Pipeline completed successfully.")
        logger.info(f"End Time: {datetime.now().isoformat()}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Critical File Missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline Failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
