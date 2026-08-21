import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_file_exists(path_str: str, description: str) -> bool:
    """Check if a required file exists."""
    path = Path(path_str)
    if path.exists():
        logger.info(f"PASS: {description} exists at {path}")
        return True
    else:
        logger.error(f"FAIL: {description} missing at {path}")
        return False

def run_script(script_path: str, args: list = None) -> bool:
    """Run a script and return True if successful."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per step
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed with exit code {e.returncode}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Script timed out")
        return False

def validate_quickstart_flow() -> bool:
    """
    Execute the quickstart.md validation flow.
    This script assumes quickstart.md documents a sequence of steps.
    We will run the critical data generation and processing steps
    to verify end-to-end reproducibility.
    """
    project_root = Path.cwd()
    if not (project_root / 'docs' / 'quickstart.md').exists():
        logger.error("docs/quickstart.md not found. Cannot validate.")
        return False

    logger.info("Starting quickstart validation flow...")
    
    # Step 1: Verify data source (T009 equivalent)
    if not run_script('code/data/validate_logs.py'):
        logger.error("Step 1 (Data Source Check) failed.")
        return False

    # Step 2: Extract Latents (T013)
    if not run_script('code/data/extract_latents.py'):
        logger.error("Step 2 (Extract Latents) failed.")
        return False

    # Step 3: Validate Thresholds (T012b)
    # Note: T012b was marked as needing redo. We run it here to ensure it works.
    if not run_script('code/tasks/validate_thresholds.py'):
        logger.error("Step 3 (Validate Thresholds) failed.")
        return False

    # Step 4: Preprocess (T014d, T014e, T014f)
    if not run_script('code/data/preprocess.py'):
        logger.error("Step 4 (Preprocess) failed.")
        return False

    # Step 5: Power Analysis & Sampling (T016, T014g, T014b)
    if not run_script('code/data/generate_power_analysis.py'):
        logger.error("Step 5 (Power Analysis) failed.")
        return False
    
    # Step 6: Model Training (T019b)
    if not run_script('code/models/trainer.py'):
        logger.error("Step 6 (Model Training) failed.")
        return False

    # Step 7: Counterfactual Indices (T047)
    if not run_script('code/data/generate_counterfactual_indices.py'):
        logger.error("Step 7 (Counterfactual Indices) failed.")
        return False

    # Step 8: Hybrid Inference (T050a, T050b)
    if not run_script('code/inference/hybrid_sim.py'):
        logger.error("Step 8 (Hybrid Simulation) failed.")
        return False

    # Step 9: Metrics Evaluation (T050c, T049, T043)
    if not run_script('code/evaluation/metrics.py'):
        logger.error("Step 9 (Metrics Evaluation) failed.")
        return False

    logger.info("Quickstart validation flow completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Validate quickstart.md reproducibility')
    parser.parse_args()

    success = validate_quickstart_flow()
    
    # Write validation report
    report_path = Path('data/logs/quickstart_validation_report.json')
    report = {
        "status": "success" if success else "failed",
        "validation_time": str(Path.cwd()),
        "checks_performed": [
            "Data Source Check",
            "Latent Extraction",
            "Threshold Validation",
            "Preprocessing",
            "Power Analysis",
            "Model Training",
            "Counterfactual Indices",
            "Hybrid Simulation",
            "Metrics Evaluation"
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")

    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
