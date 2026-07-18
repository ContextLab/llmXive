"""
End-to-End Validation Script for PROJ-509.

This script executes the full pipeline as described in quickstart.md
to ensure reproducibility. It runs:
1. Data Ingestion (ingest.py)
2. Descriptor Computation (descriptors.py)
3. Model Training (train.py)
4. Evaluation (evaluate.py)
5. Feature Importance (importance.py)
6. Plots (plots.py)

It validates that all expected output artifacts are created and non-empty.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports if needed, though we run scripts via CLI
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "data/logs/validation_run.log")
    ]
)
logger = logging.getLogger(__name__)

# Define the pipeline steps: (script_name, expected_outputs)
# Each step is a tuple of the script to run and a list of expected output paths relative to PROJECT_ROOT
PIPELINE_STEPS: List[Dict[str, Any]] = [
    {
        "name": "Ingestion",
        "script": "ingest.py",
        "expected_outputs": [
            "data/processed/sampled_raw_data.csv",
            "data/processed/sampling_manifest.json",
            "data/logs/sampling.log"
        ]
    },
    {
        "name": "Descriptors",
        "script": "descriptors.py",
        "expected_outputs": [
            "data/processed/computed_descriptors.csv",
            "data/logs/outliers.log"
        ]
    },
    {
        "name": "Training",
        "script": "train.py",
        "expected_outputs": [
            "data/evaluation/trained_models.pkl"
        ]
    },
    {
        "name": "Evaluation",
        "script": "evaluate.py",
        "expected_outputs": [
            "data/evaluation/model_metrics.json"
        ]
    },
    {
        "name": "Importance",
        "script": "importance.py",
        "expected_outputs": [
            "data/evaluation/permutation_importance.json",
            "data/evaluation/feature_ranking.json",
            "data/evaluation/vif_scores.json"
        ]
    },
    {
        "name": "Plots",
        "script": "plots.py",
        "expected_outputs": [
            "data/evaluation/pdp_plots/"  # Directory existence check
        ]
    }
]

def run_step(step: Dict[str, Any]) -> bool:
    """Run a single pipeline step and verify outputs."""
    logger.info(f"--- Running Step: {step['name']} ({step['script']}) ---")
    
    script_path = CODE_DIR / step["script"]
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=False, # Stream output to see progress
            check=True
        )
        logger.info(f"Script {step['script']} completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {step['script']} failed with return code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {step['script']}: {e}")
        return False

    # Verify outputs
    all_outputs_exist = True
    for output_path_str in step["expected_outputs"]:
        output_path = PROJECT_ROOT / output_path_str
        if output_path_str.endswith("/"):
            # Check directory
            if not output_path.exists() or not output_path.is_dir():
                logger.warning(f"Expected directory missing: {output_path}")
                all_outputs_exist = False
            else:
                logger.info(f"Verified directory: {output_path}")
        else:
            # Check file
            if not output_path.exists():
                logger.error(f"Expected output missing: {output_path}")
                all_outputs_exist = False
            else:
                # Check if file is non-empty
                if output_path.stat().st_size == 0:
                    logger.error(f"Expected output is empty: {output_path}")
                    all_outputs_exist = False
                else:
                    logger.info(f"Verified output: {output_path} ({output_path.stat().st_size} bytes)")
    
    if not all_outputs_exist:
        logger.error(f"Step {step['name']} failed output verification.")
        return False

    return True

def main():
    logger.info("Starting End-to-End Validation Pipeline...")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    all_passed = True
    for step in PIPELINE_STEPS:
        if not run_step(step):
            all_passed = False
            logger.error(f"Pipeline stopped at step: {step['name']}")
            break

    if all_passed:
        logger.info("========================================")
        logger.info("VALIDATION SUCCESSFUL")
        logger.info("All pipeline steps executed and outputs verified.")
        logger.info("========================================")
        # Print a summary of artifacts
        logger.info("Generated Artifacts Summary:")
        for step in PIPELINE_STEPS:
            logger.info(f"  {step['name']}: {step['expected_outputs']}")
        return 0
    else:
        logger.error("========================================")
        logger.error("VALIDATION FAILED")
        logger.error("One or more steps failed or outputs missing.")
        logger.error("========================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())