"""
Main Pipeline Orchestrator.
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import yaml

from utils.logging import configure_root_logger, get_module_logger
from data.ingestion import run_all_ingestion
from data.validation import run_validation_pipeline
from data.preprocessing import run_preprocessing_pipeline
from models.training import main as training_main
from models.evaluation import main as evaluation_main
from config import get_config

logger = get_module_logger(__name__)
STATE_FILE = Path("state/PROJ-475-predicting-plant-defense-compound-produc.yaml")

def update_state_file():
    """Updates the state file with current timestamp (Constitution Principle V)."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        'project_id': 'PROJ-475-predicting-plant-defense-compound-produc',
        'updated_at': datetime.now().isoformat(),
        'status': 'completed'
    }
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f)
    logger.info(f"Updated state file: {STATE_FILE}")

def run_pipeline():
    """Runs the full pipeline: Ingestion -> Validation -> Preprocessing -> Training -> Evaluation."""
    logger.info("Starting full pipeline.")
    
    # 1. Ingestion
    logger.info("Step 1: Ingestion")
    run_all_ingestion()
    
    # 2. Validation
    logger.info("Step 2: Validation")
    try:
        run_validation_pipeline()
    except SystemExit as e:
        if str(e) == "E-DATA-INSUFFICIENT":
            logger.error("Pipeline halted: Insufficient data retention.")
            return False
        raise
    
    # 3. Preprocessing (T015)
    logger.info("Step 3: Preprocessing (T015)")
    run_preprocessing_pipeline()
    
    # 4. Training
    logger.info("Step 4: Training")
    training_main()
    
    # 5. Evaluation
    logger.info("Step 5: Evaluation")
    evaluation_main()
    
    # Update State
    update_state_file()
    
    logger.info("Pipeline completed successfully.")
    return True

def main(config=None):
    """
    Entry point for the main pipeline.
    Accepts optional config argument to satisfy all call sites.
    """
    configure_root_logger()
    if config is None:
        config = get_config()
    return run_pipeline()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
