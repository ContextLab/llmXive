"""
T028: Run quickstart.md validation and verify end-to-end execution on CPU-only environment.

This script orchestrates the full pipeline execution as described in quickstart.md (or README.md Quickstart section).
It runs ingestion, splitting, training, evaluation, and analysis steps sequentially on CPU.
It verifies that all expected output artifacts are generated and non-empty.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_step(step_name: str, script_name: str, args: list = None) -> bool:
    """Execute a pipeline step and return True if successful."""
    logger.info(f"--- Running {step_name} ---")
    cmd = [sys.executable, str(CODE_DIR / script_name)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        logger.info(f"{step_name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{step_name} failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Script not found: {script_name}")
        return False

def verify_artifact(path_str: str, min_size: int = 0) -> bool:
    """Verify an artifact exists and meets minimum size requirements."""
    path = PROJECT_ROOT / path_str
    if not path.exists():
        logger.error(f"Artifact missing: {path_str}")
        return False
    if min_size > 0 and path.stat().st_size < min_size:
        logger.error(f"Artifact too small: {path_str} (size={path.stat().st_size})")
        return False
    logger.info(f"Verified artifact: {path_str} (size={path.stat().st_size})")
    return True

def main():
    logger.info("Starting End-to-End Quickstart Validation (T028)")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    
    # Set environment for CPU-only
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    logger.info("Environment: CPU-only (CUDA_VISIBLE_DEVICES=)")

    steps = [
        ("Data Ingestion", "ingest.py"),
        ("Data Validation", "validate_data.py"),
        ("Data Splitting", "split.py"),
        ("Model Training", "train.py"),
        ("Model Evaluation", "evaluate.py"),
        ("Collinearity Check", "collinearity_check.py"),
        ("Feature Attribution", "explain.py"),
        ("Sensitivity Analysis", "sensitivity.py"),
        ("Results Aggregation", "analyze_results.py"),
        ("Artifact Hashing", "hash_artifacts.py"),
    ]

    # Run pipeline steps
    for step_name, script in steps:
        if not run_step(step_name, script):
            logger.error(f"Pipeline failed at {step_name}. Aborting.")
            sys.exit(1)

    # Verify expected outputs
    logger.info("--- Verifying Artifacts ---")
    required_artifacts = [
        ("data/raw/processed.csv", 100),
        ("data/processed/splits.json", 100),
        ("data/processed/model.pt", 1000),
        ("data/processed/metrics.json", 50),
        ("data/processed/redundancy_masks.json", 50),
        ("data/processed/attribution_results.json", 50),
        ("state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml", 50),
    ]

    all_verified = True
    for artifact_path, min_size in required_artifacts:
        if not verify_artifact(artifact_path, min_size):
            all_verified = False

    if not all_verified:
        logger.error("Verification failed: Some artifacts are missing or invalid.")
        sys.exit(1)

    # Final metrics check
    metrics_path = PROJECT_ROOT / "data/processed/metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        logger.info(f"Final Metrics: {json.dumps(metrics, indent=2)}")
        if "sc001_status" in metrics:
            logger.info(f"SC-001 Status: {metrics['sc001_status']}")
    
    logger.info("Quickstart Validation Completed Successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
