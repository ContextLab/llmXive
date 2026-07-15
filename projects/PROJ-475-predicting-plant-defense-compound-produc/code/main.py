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

# Define state file path relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "PROJ-475-predicting-plant-defense-compound-produc.yaml"

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
        from data.ingestion import run_all_ingestion
        # run_all_ingestion is the correct function to trigger the full ingestion
        # It handles fetching or generating mock data based on config
        run_all_ingestion()
    except Exception as e:
        logger.error(f"Ingestion step failed: {e}")
        return False
    
    # Step 2: Validation (T013-T014)
    logger.info("Step 2: Data Validation")
    try:
        from data.validation import run_validation_pipeline
        run_validation_pipeline()
    except Exception as e:
        logger.error(f"Validation step failed: {e}")
        return False
    
    # Step 3: Preprocessing (T015-T016, T019-T021, T026)
    logger.info("Step 3: Data Preprocessing & Feature Engineering")
    try:
        from data.preprocessing import run_preprocessing_pipeline
        run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Preprocessing/Feature Engineering step failed: {e}")
        return False
    
    # Step 4: Model Training (T022-T025)
    logger.info("Step 4: Model Training")
    try:
        from models.training import train_model
        # train_model handles loading data, CV strategy, and training
        train_model()
    except Exception as e:
        logger.error(f"Model training step failed: {e}")
        return False
    
    # Step 5: Evaluation (T029-T033)
    logger.info("Step 5: Model Evaluation")
    try:
        from models.evaluation import run_permutation_test, run_sensitivity_analysis
        # Run permutation test
        run_permutation_test()
        # Run sensitivity analysis
        run_sensitivity_analysis()
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
    
    # Load configuration if a path is provided, otherwise use default
    # The 'config' argument here might be a path string or a dict, handled by load_config
    if config is not None:
        load_config(config)
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