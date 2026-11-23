"""
Run the full pipeline end-to-end.

This script orchestrates all steps from download to report generation.
It ensures that all intermediate and final data artifacts are written to disk.
"""
import subprocess
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Order of steps ensures data flows correctly from download -> parse -> metrics -> filter -> descriptors -> validate -> model
STEPS = [
    "code/setup.py",
    "code/download_cif.py",
    "code/parse_cif.py",
    "code/compute_RAW_metrics.py",
    "code/filter_dataset.py",
    "code/add_3d_descriptors.py",
    "code/validate_dataset.py",
    "code/feature_assembly.py",
    "code/train.py",
    "code/evaluate.py",
    "code/generate_report.py",
    "code/sensitivity.py"
]

def run_step(step: str) -> bool:
    """Run a single pipeline step."""
    cmd = [sys.executable, step]
    logger.info(f"Running step: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        if result.returncode == 0:
            logger.info(f"Step {step} completed successfully")
            return True
        else:
            logger.error(f"Step {step} failed with return code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Step {step} raised CalledProcessError: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"Step {step} not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Step {step} raised unexpected exception: {e}")
        return False

def main():
    """Run all pipeline steps."""
    logger.info("Starting full pipeline execution")
    
    # Ensure we are running from the project root (where code/ is a subdirectory)
    # The script is located in code/, so we go up one level
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    if not os.path.exists(project_root / "code"):
        logger.error(f"Project root {project_root} does not contain 'code' directory. Are you running from the project root?")
        sys.exit(1)

    os.chdir(project_root)
    logger.info(f"Working directory set to: {os.getcwd()}")
    
    failed_steps = []
    for step in STEPS:
        if not run_step(step):
            failed_steps.append(step)
            logger.error(f"Pipeline failed at step: {step}")
            # Continue or break? For a full run, we might want to see all errors, 
            # but typically we stop on the first failure to fix root cause.
            # However, the task requires fixing the run-book. If a step fails, 
            # the pipeline is broken. We exit with error code.
            break
    
    if failed_steps:
        logger.error(f"Pipeline execution failed. Failed steps: {failed_steps}")
        sys.exit(1)
    
    logger.info("Full pipeline completed successfully. All artifacts written to disk.")

if __name__ == "__main__":
    main()