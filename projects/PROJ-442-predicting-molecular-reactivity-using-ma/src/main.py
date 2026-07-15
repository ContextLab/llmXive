"""
Orchestration script for the molecular reactivity prediction pipeline.
Executes major stages (Ingestion, Preprocessing, Training, Evaluation) and
updates the project state after each stage completes successfully.
"""
import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from scripts.update_state import main as update_state_main
from src.data.ingestion import main as ingestion_main
from src.data.preprocessing import main as preprocessing_main
# Importing train and evaluate stubs if they exist, otherwise we define logic here
# Assuming these modules will be created in subsequent tasks
try:
    from src.modeling.train import main as train_main
except ImportError:
    train_main = None
try:
    from src.modeling.evaluate import main as evaluate_main
except ImportError:
    evaluate_main = None

STAGES = {
    "ingestion": {
        "func": ingestion_main,
        "artifact_path": "data/processed/filtered_reactions.csv",
        "description": "Data Ingestion and Filtering"
    },
    "preprocessing": {
        "func": preprocessing_main,
        "artifact_path": "data/processed/feature_matrix.parquet",
        "description": "Feature Extraction and Preprocessing"
    },
    "training": {
        "func": train_main,
        "artifact_path": "data/models/xgboost_model.json",
        "description": "Model Training"
    },
    "evaluation": {
        "func": evaluate_main,
        "artifact_path": "data/processed/analysis_report.json",
        "description": "Model Evaluation and Analysis"
    }
}

def run_stage(stage_name: str, logger: logging.Logger) -> bool:
    """
    Executes a specific pipeline stage and updates the state.

    Args:
        stage_name: Key in STAGES dictionary.
        logger: Logger instance.

    Returns:
        True if stage succeeded, False otherwise.
    """
    if stage_name not in STAGES:
        logger.error(f"Unknown stage: {stage_name}")
        return False

    stage_config = STAGES[stage_name]
    func = stage_config["func"]
    artifact_path = stage_config["artifact_path"]
    description = stage_config["description"]

    logger.info(f"--- Starting Stage: {description} ({stage_name}) ---")

    if func is None:
        logger.warning(f"Stage {stage_name} implementation not found. Skipping.")
        # Update state to 'skipped' or 'failed' depending on policy
        # For now, we assume it's a placeholder and we should fail the pipeline
        # unless explicitly told to skip.
        update_stage_status(stage_name, "skipped", "Implementation missing")
        return False

    try:
        # Execute the stage
        func()

        # Check if artifact exists
        artifact_full_path = project_root / artifact_path
        if not artifact_full_path.exists():
            logger.error(f"Stage {stage_name} completed but artifact not found: {artifact_path}")
            update_stage_status(stage_name, "failed", "Artifact not generated")
            return False

        # Register artifact
        register_artifact(artifact_path)

        # Update stage status to completed
        update_stage_status(stage_name, "completed", "Stage finished successfully")

        # Explicitly call the state update script as requested by T009
        # This ensures the external state file is flushed and checksums updated
        logger.info(f"Calling scripts/update_state.py for stage {stage_name}...")
        update_state_main(stage_name)

        logger.info(f"--- Stage {description} completed successfully. ---")
        return True

    except Exception as e:
        logger.error(f"Stage {stage_name} failed with exception: {e}", exc_info=True)
        update_stage_status(stage_name, "failed", str(e))
        return False

def main():
    parser = argparse.ArgumentParser(description="Molecular Reactivity Pipeline Orchestration")
    parser.add_argument(
        "--stage",
        type=str,
        choices=list(STAGES.keys()) + ["all"],
        default="all",
        help="Stage to run. Default is 'all'."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("pipeline_orchestrator", log_level=args.log_level)
    logger.info("Starting Pipeline Orchestration")

    stages_to_run = [args.stage] if args.stage != "all" else list(STAGES.keys())

    success = True
    for stage in stages_to_run:
        if not run_stage(stage, logger):
            success = False
            logger.error(f"Pipeline failed at stage: {stage}")
            break

    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()