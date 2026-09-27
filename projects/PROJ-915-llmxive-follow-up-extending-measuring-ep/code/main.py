"""
code/main.py
Orchestrates the full pipeline sequence:
Ingestion -> Features -> Human Pilot -> Inference -> Labeling -> Modeling.
"""

import logging
import sys
import time
from pathlib import Path
from config import get_config
from validation import start_pipeline_timer, stop_pipeline_timer, check_pipeline_limit, enforce_pipeline_limit

logger = logging.getLogger(__name__)

def run_ingestion():
    """Run T013: Ingestion."""
    logger.info("Running Ingestion (T013)...")
    from ingestion import main as ingestion_main
    ingestion_main()

def run_features():
    """Run T014 & T015: Feature Extraction and Undefined Ratio Handling."""
    logger.info("Running Feature Extraction (T014, T015)...")
    from features import main as features_main
    features_main()

def run_human_pilot():
    """Run T017a-e: Human Pilot (Skipped if not available)."""
    logger.info("Running Human Pilot (T017a-e)...")
    # This is a placeholder for the human pilot logic.
    # In a real scenario, this would invoke annotation.py.
    # Since T017a-e are manual or require external data, we skip for now.
    logger.warning("Human Pilot stage skipped (requires manual intervention or external data).")

def run_inference():
    """Run T020-T025: Inference and Labeling."""
    logger.info("Running Inference and Labeling (T020-T025)...")
    # Placeholder for inference logic
    logger.warning("Inference and Labeling stage skipped (requires model access and fact retrieval).")

def run_modeling():
    """Run T029-T046: Modeling and Analysis."""
    logger.info("Running Modeling (T029-T046)...")
    from modeling import main as modeling_main
    modeling_main()

def main():
    """Main orchestration function."""
    config = get_config()
    start_pipeline_timer()

    try:
        logger.info("Starting Pipeline...")

        # 1. Ingestion
        run_ingestion()
        check_pipeline_limit()

        # 2. Features
        run_features()
        check_pipeline_limit()

        # 3. Human Pilot
        run_human_pilot()
        check_pipeline_limit()

        # 4. Inference & Labeling
        run_inference()
        check_pipeline_limit()

        # 5. Modeling
        run_modeling()
        check_pipeline_limit()

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        stop_pipeline_timer()
        enforce_pipeline_limit()

if __name__ == '__main__':
    main()
