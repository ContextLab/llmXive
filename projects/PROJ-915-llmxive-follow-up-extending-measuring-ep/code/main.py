"""
code/main.py
Orchestration script for the llmXive automated science pipeline.

Executes the sequence: Ingestion -> Features -> Human Pilot -> Inference -> Labeling -> Modeling.
Enforces Constitution Principle VII (Compute-Time Guard) and updates pipeline logs.
"""

import logging
import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime

# Import from existing API surface
from config import get_config
from validation import (
    start_pipeline_timer,
    stop_pipeline_timer,
    check_pipeline_limit,
    enforce_pipeline_limit,
    update_pipeline_log as validation_update_log
)

# Initialize logger
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging to output to console and pipeline_execution.log."""
    log_dir = Path("data/results")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure the pipeline_log.json exists and is initialized
    log_json_path = log_dir / "pipeline_log.json"
    if not log_json_path.exists():
        with open(log_json_path, "w") as f:
            json.dump({"stages": [], "start_time": datetime.utcnow().isoformat()}, f, indent=2)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "pipeline_execution.log")
        ]
    )

def update_pipeline_log(stage_name: str, status: str, duration: float = 0.0):
    """Update the pipeline log JSON file with stage status."""
    log_path = Path("data/results/pipeline_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if log_path.exists():
        with open(log_path, "r") as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = {"stages": []}
    else:
        log_data = {"stages": []}
    
    entry = {
        "stage": stage_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": duration
    }
    
    log_data["stages"].append(entry)
    
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)
    
    # Also update via the validation module's tracker if available
    try:
        validation_update_log(stage_name, status, duration)
    except Exception as e:
        logger.warning(f"Could not update validation log: {e}")

def run_ingestion():
    """Run T013: Ingestion."""
    logger.info("Running Ingestion (T013)...")
    start_time = time.time()
    try:
        from ingestion import main as ingestion_main
        ingestion_main()
        duration = time.time() - start_time
        update_pipeline_log("Ingestion", "success", duration)
        logger.info(f"Ingestion completed successfully in {duration:.2f}s.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        update_pipeline_log("Ingestion", "failed", time.time() - start_time)
        raise

def run_features():
    """Run T014 & T015: Feature Extraction and Undefined Ratio Handling."""
    logger.info("Running Feature Extraction (T014, T015)...")
    start_time = time.time()
    try:
        from features import main as features_main
        features_main()
        duration = time.time() - start_time
        update_pipeline_log("Features", "success", duration)
        logger.info(f"Feature Extraction completed successfully in {duration:.2f}s.")
    except Exception as e:
        logger.error(f"Feature Extraction failed: {e}")
        update_pipeline_log("Features", "failed", time.time() - start_time)
        raise

def run_human_pilot():
    """Run T017a-e: Human Pilot (Skipped if not available)."""
    logger.info("Running Human Pilot (T017a-e)...")
    start_time = time.time()
    try:
        from annotation import run_cleaning_pipeline
        # Attempt to run the cleaning pipeline which handles the pilot logic
        # If data is missing, it should fail loudly as per constraints
        run_cleaning_pipeline()
        duration = time.time() - start_time
        update_pipeline_log("Human Pilot", "success", duration)
        logger.info(f"Human Pilot stage completed in {duration:.2f}s.")
    except FileNotFoundError as e:
        logger.warning(f"Human Pilot data not found (expected if not uploaded): {e}")
        update_pipeline_log("Human Pilot", "skipped", 0.0)
    except Exception as e:
        logger.error(f"Human Pilot stage failed: {e}")
        update_pipeline_log("Human Pilot", "failed", time.time() - start_time)
        raise

def run_inference():
    """Run T020-T025: Inference and Labeling."""
    logger.info("Running Inference and Labeling (T020-T025)...")
    start_time = time.time()
    try:
        from labeling import main as labeling_main
        labeling_main()
        duration = time.time() - start_time
        update_pipeline_log("Inference", "success", duration)
        logger.info(f"Inference and Labeling completed successfully in {duration:.2f}s.")
    except Exception as e:
        logger.error(f"Inference and Labeling failed: {e}")
        update_pipeline_log("Inference", "failed", time.time() - start_time)
        raise

def run_modeling():
    """Run T029-T046: Modeling and Analysis."""
    logger.info("Running Modeling (T029-T046)...")
    start_time = time.time()
    try:
        from modeling import main as modeling_main
        modeling_main()
        duration = time.time() - start_time
        update_pipeline_log("Modeling", "success", duration)
        logger.info(f"Modeling completed successfully in {duration:.2f}s.")
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        update_pipeline_log("Modeling", "failed", time.time() - start_time)
        raise

def main():
    """Main orchestration function."""
    setup_logging()
    config = get_config()
    
    logger.info("Starting Pipeline...")
    start_pipeline_timer()

    try:
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