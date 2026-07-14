"""
Main pipeline orchestrator.
Executes: Ingestion -> Validation -> Preprocessing -> Training -> Evaluation.
Updates state file upon completion.
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import yaml

# Add code directory to path for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_config
from data.ingestion import main as run_ingestion
from data.validation import main as run_validation
from data.preprocessing import main as run_preprocessing
from models.training import main as run_training
from models.evaluation import main as run_evaluation
from utils.logging import configure_root_logger, get_module_logger
from utils.io import check_disk_space

def update_state_file(config):
    """Update the state file with the current timestamp."""
    state_dir = Path(config.paths.state)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-475-predicting-plant-defense-compound-produc.yaml"
    
    state_data = {
        "project_id": "PROJ-475-predicting-plant-defense-compound-produc",
        "updated_at": datetime.now().isoformat(),
        "status": "completed"
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger = get_module_logger(__name__)
    logger.info(f"State file updated: {state_file}")

def run_pipeline(config):
    """Execute the full research pipeline."""
    logger = get_module_logger(__name__)
    logger.info("Starting full pipeline...")
    
    # Check disk space before starting
    estimated_size = 2 * 1024 * 1024 * 1024 # 2GB estimate
    check_disk_space(estimated_size)
    
    try:
        # 1. Ingestion
        logger.info("Step 1: Ingestion")
        run_ingestion(config)
        
        # 2. Validation
        logger.info("Step 2: Validation")
        run_validation(config)
        
        # 3. Preprocessing
        logger.info("Step 3: Preprocessing")
        run_preprocessing(config)
        
        # 4. Training
        logger.info("Step 4: Training")
        run_training(config)
        
        # 5. Evaluation
        logger.info("Step 5: Evaluation")
        run_evaluation(config)
        
        logger.info("Pipeline completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False

def main():
    configure_root_logger()
    config = get_config()
    
    success = run_pipeline(config)
    
    if success:
        update_state_file(config)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
