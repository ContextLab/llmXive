"""
Main Orchestrator for the Plant Defense Compound Prediction Pipeline.
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import yaml

from config import get_config
from utils.logging import configure_root_logger, get_module_logger
from data.ingestion import run_ingestion_pipeline
from data.validation import run_validation_pipeline
from data.preprocessing import run_vif_analysis, aggregate_to_population_level
from models.training import train_model, extract_top_predictors
from models.evaluation import run_permutation_test, run_sensitivity_analysis
from scripts.update_manifest import update_manifest

logger = get_module_logger(__name__)

def update_state_file(state_path: str = "state/PROJ-475-predicting-plant-defense-compound-produc.yaml") -> None:
    """Updates the state file with the current timestamp."""
    state_file = Path(state_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    current_state = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            current_state = yaml.safe_load(f) or {}
    
    current_state['updated_at'] = datetime.now().isoformat()
    current_state['status'] = 'running'
    
    with open(state_file, 'w') as f:
        yaml.dump(current_state, f)

def run_pipeline() -> int:
    """
    Runs the full pipeline: Ingestion -> Validation -> Feature Eng -> Training -> Evaluation.
    """
    logger.info("Starting full pipeline...")
    update_state_file()
    
    try:
        # Step 1: Ingestion
        logger.info("Step 1: Ingestion")
        run_ingestion_pipeline()
        
        # Step 2: Validation
        logger.info("Step 2: Validation")
        run_validation_pipeline()
        
        # Step 3: Feature Engineering (VIF, Aggregation)
        logger.info("Step 3: Feature Engineering")
        aggregate_to_population_level()
        run_vif_analysis()
        
        # Step 4: Training
        logger.info("Step 4: Training")
        model = train_model()
        extract_top_predictors(model)
        
        # Step 5: Evaluation
        logger.info("Step 5: Evaluation")
        run_permutation_test()
        run_sensitivity_analysis()
        
        # Update Manifest
        logger.info("Updating Manifest")
        update_manifest()
        
        update_state_file()
        with open("state/PROJ-475-predicting-plant-defense-compound-produc.yaml", 'r') as f:
            state = yaml.safe_load(f)
            state['status'] = 'completed'
        with open("state/PROJ-475-predicting-plant-defense-compound-produc.yaml", 'w') as f:
            yaml.dump(state, f)
        
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main() -> int:
    """
    CLI entry point.
    """
    configure_root_logger()
    return run_pipeline()

if __name__ == "__main__":
    sys.exit(main())