"""
Main Pipeline Orchestrator.
Orchestrates: Ingestion -> Validation -> Preprocessing -> Training -> Evaluation.
Updates state file upon completion (Constitution Principle V).
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

def update_state_file():
    """Updates the state file with current timestamp (Constitution Principle V)."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Load existing state if present to preserve other keys, otherwise start fresh
    state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                state = yaml.safe_load(f) or {}
        except Exception:
            state = {}
    
    state['project_id'] = 'PROJ-475-predicting-plant-defense-compound-produc'
    state['updated_at'] = datetime.now().isoformat()
    state['status'] = 'completed'
    
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f)
    logger.info(f"Updated state file: {STATE_FILE}")

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

def main(config=None, *args, **kwargs):
    """
    Entry point for the main pipeline.
    Accepts optional config argument and *args/**kwargs to satisfy all call sites.
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
    success = main()
    sys.exit(0 if success else 1)