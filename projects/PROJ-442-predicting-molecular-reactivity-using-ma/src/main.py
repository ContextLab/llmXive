"""
Main orchestration script for the Molecular Reactivity Prediction pipeline.

This script coordinates the major stages of the research pipeline:
1. Data Ingestion (US1)
2. Feature Extraction & Preprocessing (US2)
3. Model Training (US2)
4. Evaluation & Analysis (US3)

After each major stage, it updates the project state via scripts/update_state.py.
"""
import argparse
import sys
import os
import logging
import subprocess
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logging import setup_logging
from src.utils.state_manager import update_state

# Configure logging
logger = setup_logging(__name__)

def run_stage(stage_name: str, script_path: str, args: list = None) -> bool:
    """
    Execute a pipeline stage script and update state upon success.
    
    Args:
        stage_name: Human-readable name of the stage
        script_path: Path to the script to execute (relative to project root)
        args: Optional list of command-line arguments
    
    Returns:
        True if stage completed successfully, False otherwise
    """
    logger.info(f"Starting stage: {stage_name}")
    start_time = datetime.now()
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Stage '{stage_name}' completed successfully in {elapsed:.2f}s")
        
        # Update state after successful stage
        update_state(
            stage=stage_name,
            status="completed",
            duration_seconds=elapsed,
            script_path=script_path
        )
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Stage '{stage_name}' failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        
        # Update state with failure
        update_state(
            stage=stage_name,
            status="failed",
            error=str(e),
            script_path=script_path
        )
        
        return False
    except Exception as e:
        logger.error(f"Stage '{stage_name}' encountered an unexpected error: {e}")
        update_state(
            stage=stage_name,
            status="failed",
            error=str(e),
            script_path=script_path
        )
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate the Molecular Reactivity Prediction pipeline"
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["ingestion", "preprocessing", "training", "evaluation"],
        choices=["ingestion", "preprocessing", "training", "evaluation", "all"],
        help="Stages to execute (default: all)"
    )
    parser.add_argument(
        "--skip-state-update",
        action="store_true",
        help="Skip state updates after stages"
    )
    
    args = parser.parse_args()
    
    # Determine stages to run
    if "all" in args.stages or len(args.stages) == 4:
        stages_to_run = ["ingestion", "preprocessing", "training", "evaluation"]
    else:
        stages_to_run = args.stages
    
    logger.info(f"Pipeline execution starting. Stages: {stages_to_run}")
    
    # Define stage scripts and their dependencies
    stage_scripts = {
        "ingestion": {
            "script": "src/data/ingestion.py",
            "description": "Download and filter USPTO reaction data"
        },
        "preprocessing": {
            "script": "src/data/preprocessing.py",
            "description": "Extract molecular features and perform dimensionality reduction"
        },
        "training": {
            "script": "src/modeling/train.py",
            "description": "Train XGBoost model with cross-validation"
        },
        "evaluation": {
            "script": "src/modeling/evaluate.py",
            "description": "Evaluate model performance and generate analysis report"
        }
    }
    
    success = True
    for stage in stages_to_run:
        if stage not in stage_scripts:
            logger.error(f"Unknown stage: {stage}")
            success = False
            continue
        
        logger.info(f"Executing: {stage_scripts[stage]['description']}")
        
        if not run_stage(
            stage_name=stage,
            script_path=stage_scripts[stage]["script"]
        ):
            success = False
            logger.error(f"Pipeline stopped due to failure in stage: {stage}")
            break
    
    if success:
        logger.info("Pipeline execution completed successfully!")
        return 0
    else:
        logger.error("Pipeline execution failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
