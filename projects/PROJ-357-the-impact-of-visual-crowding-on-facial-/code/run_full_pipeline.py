"""
Run the full analysis pipeline for the visual crowding study.

This script orchestrates the execution of all pipeline steps in the correct order,
from data download through final validation.

Usage:
    python code/run_full_pipeline.py [--seed SEED]
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from config import set_all_seeds, ensure_directories, get_seed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Configure logging for the pipeline execution."""
    log_dir = project_root / "data" / "interim"
    ensure_directories([log_dir])
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline_execution.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_step(step_name, script_path, args=None):
    """
    Run a pipeline step as a subprocess.
    
    Args:
        step_name (str): Name of the step for logging.
        script_path (str): Path to the script to execute.
        args (list, optional): Additional command-line arguments.
        
    Returns:
        bool: True if step succeeded, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"--- Starting step: {step_name} ---")
    
    cmd = [sys.executable, str(project_root / script_path)]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        import subprocess
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            capture_output=False
        )
        logger.info(f"Step '{step_name}' completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step '{step_name}' failed with return code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Step '{step_name}' failed with exception: {e}")
        return False

def main():
    """Main entry point for the full pipeline."""
    parser = argparse.ArgumentParser(description="Run the full visual crowding analysis pipeline")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: from config)")
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting full pipeline execution")
    
    # Set seed
    seed = args.seed if args.seed is not None else get_seed()
    set_all_seeds(seed)
    logger.info(f"Random seed set to {seed}")
    
    # Define pipeline steps in order
    pipeline_steps = [
        ("Download RAVDESS dataset", "code/utils/download.py"),
        ("Extract frames from videos", "code/utils/frame_extractor.py"),
        ("Generate stimuli", "code/utils/stimulus_gen.py"),
        ("Generate stimuli manifest", "code/utils/stimuli_manifest.py"),
        ("Validate manifest completeness", "code/utils/manifest_validator.py"),
        ("Compute clutter metrics", "code/utils/clutter_metrics.py"),
        # Note: Human pilot data collection (T047) is manual and should be done separately
        # If synthetic data is needed for testing, use: code/analysis/generate_synthetic_data.py
        ("Aggregate human judgments", "code/analysis/aggregate_judgments.py"),
        ("Fit GLMM model", "code/analysis/glmm_model.py"),
        ("Write regression results", "code/analysis/write_regression_results.py"),
        ("Write model config", "code/analysis/write_model_config.py"),
        ("Generate associational report", "code/analysis/reporting.py"),
        ("Generate validation report", "code/analysis/validation_report.py"),
    ]
    
    failed_steps = []
    
    for step_name, script_path in pipeline_steps:
        # Check if the step requires manual intervention (e.g., human pilot)
        # For now, we'll skip steps that might fail due to missing manual data
        # and log a warning instead
        if "human pilot" in step_name.lower() or "collect" in step_name.lower():
            logger.warning(f"Skipping manual step: {step_name}")
            continue
            
        success = run_step(step_name, script_path)
        if not success:
            failed_steps.append(step_name)
            # Continue execution to see all failures, or uncomment below to stop
            # logger.error("Pipeline stopped due to failure")
            # break
    
    # Summary
    if failed_steps:
        logger.error(f"Pipeline completed with {len(failed_steps)} failures:")
        for step in failed_steps:
            logger.error(f"  - {step}")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully - all steps passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
