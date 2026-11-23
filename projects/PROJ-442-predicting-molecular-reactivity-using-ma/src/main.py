"""
Orchestration script for the molecular reactivity prediction pipeline.
Executes major stages (Ingestion, Preprocessing, Training, Evaluation) and
updates the project state after each stage completion.
"""
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List, Optional

# Project imports based on API surface
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact, get_state

# Stage-specific imports
from src.data.ingestion import main as run_ingestion
from src.data.preprocessing import main as run_preprocessing
from src.modeling.train import main as run_training
from scripts.update_state import main as run_update_state_script


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the molecular reactivity prediction pipeline."
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["ingestion", "preprocessing", "training", "evaluation", "all"],
        default=["all"],
        help="Stages to execute. Default is 'all'.",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="PROJ-442-predicting-molecular-reactivity-using-ma",
        help="Project ID for state management.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser.parse_args()


def run_stage(stage_name: str, logger: logging.Logger) -> bool:
    """
    Execute a specific pipeline stage.
    
    Args:
        stage_name: Name of the stage to run.
        logger: Logger instance.
        
    Returns:
        True if stage completed successfully, False otherwise.
    """
    logger.info(f"Starting stage: {stage_name}")
    
    try:
        if stage_name == "ingestion":
            # Run ingestion script
            run_ingestion()
            artifact_path = "data/processed/filtered_reactions.csv"
            register_artifact(artifact_path, stage_name)
            update_stage_status(stage_name, "completed", artifact_path)
            
        elif stage_name == "preprocessing":
            # Run preprocessing script
            run_preprocessing()
            artifact_path = "data/processed/feature_matrix.parquet"
            register_artifact(artifact_path, stage_name)
            update_stage_status(stage_name, "completed", artifact_path)
            
        elif stage_name == "training":
            # Run training script
            run_training()
            model_path = "data/models/xgboost_model.json"
            log_path = "data/processed/training_log.json"
            register_artifact(model_path, stage_name)
            register_artifact(log_path, stage_name)
            update_stage_status(stage_name, "completed", model_path)
            
        elif stage_name == "evaluation":
            # Note: Evaluation module not fully implemented yet in this task scope
            # Placeholder for future implementation
            logger.warning("Evaluation stage not yet implemented. Skipping.")
            update_stage_status(stage_name, "skipped", None)
            
        else:
            logger.error(f"Unknown stage: {stage_name}")
            return False
            
        logger.info(f"Stage {stage_name} completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Stage {stage_name} failed with error: {str(e)}")
        update_stage_status(stage_name, "failed", None)
        return False


def main() -> int:
    """Main entry point for the orchestration script."""
    args = parse_args()
    
    # Setup logging
    logger = setup_logger(
        name="pipeline_orchestrator",
        log_level=args.log_level,
        log_file="logs/pipeline_orchestrator.log"
    )
    
    logger.info(f"Starting pipeline orchestration for project: {args.project_id}")
    
    # Determine stages to run
    stages_to_run = []
    if "all" in args.stages:
        stages_to_run = ["ingestion", "preprocessing", "training", "evaluation"]
    else:
        stages_to_run = args.stages
    
    # Execute stages
    success = True
    for stage in stages_to_run:
        if not run_stage(stage, logger):
            logger.error(f"Pipeline failed at stage: {stage}")
            success = False
            break
    
    # Final state update via scripts/update_state.py
    if success:
        logger.info("All stages completed. Updating final state.")
        # Call the external update_state script to ensure consistency
        run_update_state_script()
    else:
        logger.warning("Pipeline encountered errors. State updated accordingly.")
    
    logger.info("Pipeline orchestration finished.")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())