"""
Main pipeline orchestrator for predicting plant defense compound production.

This script executes the full research pipeline:
1. Ingestion (Genomic, Environmental, Compound data)
2. Validation (Merging, Listwise deletion, Retention check)
3. Feature Engineering (Diversity metrics, Aggregation, VIF, Normalization)
4. Model Training (CV strategy selection, LASSO/Ridge training, Top predictors)
5. Evaluation (Permutation test, Sensitivity analysis, Jaccard stability, BH correction)

It also updates the project state file (Constitution Principle V) upon completion.
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
import yaml

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, ConfigError
from utils.logging import get_module_logger, configure_root_logger
from utils.io import check_disk_space, DiskSpaceError
from data.ingestion import main as ingestion_main
from data.validation import main as validation_main
from data.preprocessing import main as preprocessing_main
from models.training import main as training_main
from models.evaluation import main as evaluation_main

logger = get_module_logger(__name__)

def update_state_file(state_path: Path) -> None:
    """
    Updates the project state YAML file with the current timestamp.
    Implements Constitution Principle V: Auditability and State Tracking.
    """
    state_file = project_root / state_path
    
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    current_state = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                current_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}. Starting fresh.")
            current_state = {}

    # Update timestamp
    current_state['updated_at'] = datetime.now().isoformat()
    current_state['last_task'] = 'T034'
    current_state['status'] = 'completed'

    with open(state_file, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file updated: {state_file}")

def run_pipeline() -> int:
    """
    Orchestrates the full pipeline execution.
    Returns 0 on success, non-zero on failure.
    """
    configure_root_logger()
    logger.info("Starting Plant Defense Compound Prediction Pipeline (T034)")

    try:
        config = get_config()
        logger.info("Configuration loaded successfully")

        # Check disk space before starting heavy operations
        estimated_size = config.get('disk_space_estimation_gb', 5.0) * 1024**3
        check_disk_space(estimated_size)
        logger.info(f"Disk space check passed (estimated need: {estimated_size / 1024**3:.2f} GB)")

        # 1. Ingestion
        logger.info("Step 1: Starting Data Ingestion...")
        ingestion_main()
        logger.info("Step 1: Ingestion complete.")

        # 2. Validation
        logger.info("Step 2: Starting Data Validation...")
        validation_main()
        logger.info("Step 2: Validation complete.")

        # 3. Feature Engineering
        logger.info("Step 3: Starting Feature Engineering...")
        preprocessing_main()
        logger.info("Step 3: Feature Engineering complete.")

        # 4. Model Training
        logger.info("Step 4: Starting Model Training...")
        training_main()
        logger.info("Step 4: Model Training complete.")

        # 5. Evaluation
        logger.info("Step 5: Starting Model Evaluation...")
        evaluation_main()
        logger.info("Step 5: Evaluation complete.")

        # Constitution Principle V: Update State
        logger.info("Updating project state (Constitution Principle V)...")
        state_path = Path("state/PROJ-475-predicting-plant-defense-compound-produc.yaml")
        update_state_file(state_path)

        logger.info("Pipeline completed successfully.")
        return 0

    except DiskSpaceError as e:
        logger.error(f"Disk space insufficient: {e}")
        return 1
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 2
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 3
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        return 99

def main():
    """Entry point for the pipeline."""
    sys.exit(run_pipeline())

if __name__ == "__main__":
    main()