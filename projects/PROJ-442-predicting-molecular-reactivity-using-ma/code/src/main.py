"""
Main orchestration script for the Molecular Reactivity Prediction Pipeline.

This script coordinates the major stages of the pipeline:
1. Data Ingestion
2. Feature Extraction
3. Model Training
4. Model Evaluation

After each major stage, it updates the project state via scripts/update_state.py.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact

# Configure logger
logger = setup_logger("main_orchestrator")

# Define stage names and their corresponding script paths
STAGES = [
    {
        "name": "ingestion",
        "script": "src/data/ingestion.py",
        "output_artifacts": ["data/processed/filtered_reactions.csv"],
        "description": "Download and filter USPTO reaction data"
    },
    {
        "name": "preprocessing",
        "script": "src/data/preprocessing.py",
        "output_artifacts": ["data/processed/feature_matrix.parquet"],
        "description": "Extract molecular features and reduce dimensionality"
    },
    {
        "name": "training",
        "script": "src/modeling/train.py",
        "output_artifacts": ["data/models/xgboost_model.json", "data/processed/training_log.json"],
        "description": "Train XGBoost model with cross-validation"
    },
    {
        "name": "evaluation",
        "script": "src/modeling/evaluate.py",
        "output_artifacts": ["data/processed/analysis_report.json"],
        "description": "Evaluate model performance and generate report"
    }
]

def run_stage(stage_config: dict) -> bool:
    """
    Execute a single pipeline stage.

    Args:
        stage_config: Dictionary containing stage configuration

    Returns:
        bool: True if stage completed successfully, False otherwise
    """
    stage_name = stage_config["name"]
    script_path = stage_config["script"]
    description = stage_config["description"]
    output_artifacts = stage_config["output_artifacts"]

    logger.info(f"Starting stage: {stage_name} - {description}")

    # Update state to indicate stage started
    update_stage_status(stage_name, "running")

    try:
        # Construct and execute the script command
        full_script_path = project_root / script_path
        if not full_script_path.exists():
            logger.error(f"Script not found: {full_script_path}")
            return False

        # Execute the script
        logger.info(f"Executing: python {full_script_path}")
        exit_code = os.system(f"python {full_script_path}")

        if exit_code != 0:
            logger.error(f"Stage {stage_name} failed with exit code {exit_code}")
            update_stage_status(stage_name, "failed")
            return False

        # Register output artifacts and update state
        for artifact_path in output_artifacts:
            full_artifact_path = project_root / artifact_path
            if full_artifact_path.exists():
                register_artifact(artifact_path)
            else:
                logger.warning(f"Expected artifact not found: {full_artifact_path}")

        update_stage_status(stage_name, "completed")
        logger.info(f"Stage {stage_name} completed successfully")
        return True

    except Exception as e:
        logger.exception(f"Unexpected error during stage {stage_name}: {e}")
        update_stage_status(stage_name, "failed")
        return False

def main():
    """Main entry point for the pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Molecular Reactivity Prediction Pipeline")
    logger.info("=" * 60)

    # Update initial state
    update_stage_status("pipeline_start", "running")

    all_success = True
    for stage in STAGES:
        if not run_stage(stage):
            all_success = False
            logger.error(f"Pipeline failed at stage: {stage['name']}")
            break

    # Final state update
    if all_success:
        update_stage_status("pipeline_complete", "completed")
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        return 0
    else:
        update_stage_status("pipeline_complete", "failed")
        logger.error("=" * 60)
        logger.error("Pipeline failed. Check logs for details.")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())