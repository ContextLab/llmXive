"""
Main entry point for the plant defense compound prediction pipeline.

Orchestrates the full pipeline: Ingestion → Validation → Preprocessing → 
Feature Engineering → Model Training → Evaluation.

Constitution Principle V: Updates state file with timestamp upon completion.
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import yaml

from utils.logging import configure_root_logger, get_module_logger
from config import load_config, get_config

logger = get_module_logger(__name__)

def update_state_file(state_path: str = "state/PROJ-475-predicting-plant-defense-compound-produc.yaml"):
    """
    Update the state file with current timestamp and completion status.
    
    Constitution Principle V: Record pipeline completion.
    """
    state_file = Path(state_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    current_state = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            current_state = yaml.safe_load(f) or {}
    
    current_state['updated_at'] = datetime.now().isoformat()
    current_state['last_run_status'] = 'success'
    current_state['pipeline_version'] = '1.0.0'
    
    with open(state_file, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False)
    
    logger.info(f"Updated state file: {state_path}")

def run_pipeline():
    """
    Execute the full research pipeline.
    """
    logger.info("Starting full research pipeline")
    
    # Step 1: Ingestion (T010-T012)
    logger.info("Step 1: Data Ingestion")
    try:
        from data.ingestion import main as ingestion_main
        if ingestion_main() != 0:
            logger.error("Ingestion step failed")
            return False
    except Exception as e:
        logger.error(f"Ingestion step failed: {e}")
        return False
    
    # Step 2: Validation (T013-T014)
    logger.info("Step 2: Data Validation")
    try:
        from data.validation import main as validation_main
        if validation_main() != 0:
            logger.error("Validation step failed")
            return False
    except Exception as e:
        logger.error(f"Validation step failed: {e}")
        return False
    
    # Step 3: Preprocessing (T015-T016)
    logger.info("Step 3: Data Preprocessing")
    try:
        from data.preprocessing import main as preprocessing_main
        if preprocessing_main() != 0:
            logger.error("Preprocessing step failed")
            return False
    except Exception as e:
        logger.error(f"Preprocessing step failed: {e}")
        return False
    
    # Step 4: Feature Engineering (T019-T021, T026)
    logger.info("Step 4: Feature Engineering")
    try:
        # T019, T020, T021, T026 are part of preprocessing module
        # Re-run preprocessing with feature engineering steps if needed
        from data.preprocessing import run_preprocessing_pipeline
        run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Feature engineering step failed: {e}")
        return False
    
    # Step 5: Model Training (T022-T025)
    logger.info("Step 5: Model Training")
    try:
        from models.training import main as training_main
        if training_main() != 0:
            logger.error("Model training step failed")
            return False
    except Exception as e:
        logger.error(f"Model training step failed: {e}")
        return False
    
    # Step 6: Evaluation (T029-T033)
    logger.info("Step 6: Model Evaluation")
    try:
        from models.evaluation import main as evaluation_main
        if evaluation_main() != 0:
            logger.error("Model evaluation step failed")
            return False
    except Exception as e:
        logger.error(f"Model evaluation step failed: {e}")
        return False
    
    logger.info("Full pipeline completed successfully")
    return True

def main(config_path: Optional[str] = None):
    """
    Main entry point.
    
    Args:
        config_path: Optional path to configuration file.
    """
    configure_root_logger()
    
    # Load configuration
    if config_path:
        load_config(config_path)
    else:
        get_config()  # Load default config
    
    success = run_pipeline()
    
    if success:
        update_state_file()
        logger.info("Pipeline execution completed successfully")
        return 0
    else:
        logger.error("Pipeline execution failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
