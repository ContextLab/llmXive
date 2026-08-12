"""
Quickstart Validation Module for PROJ-509.

This module orchestrates the end-to-end reproducibility check of the research pipeline
as defined in the project's quickstart documentation. It executes the pipeline steps
sequentially and verifies the existence and integrity of expected artifacts.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging import setup_logging, get_logger
from config import load_paths


def run_step(step_name: str, command: List[str], cwd: Optional[Path] = None) -> bool:
    """
    Executes a single pipeline step and returns success status.

    Args:
        step_name: Human-readable name of the step for logging.
        command: List of arguments for subprocess.run.
        cwd: Working directory for the command. Defaults to project root.

    Returns:
        True if the command exits with code 0, False otherwise.
    """
    logger = get_logger()
    logger.info(f"--- Executing Step: {step_name} ---")
    logger.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"Step '{step_name}' completed successfully.")
            if result.stdout:
                logger.debug(f"stdout: {result.stdout}")
            return True
        else:
            logger.error(f"Step '{step_name}' failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"stderr: {result.stderr}")
            if result.stdout:
                logger.error(f"stdout: {result.stdout}")
            return False

    except FileNotFoundError as e:
        logger.error(f"Step '{step_name}' failed: Command not found. {e}")
        return False
    except Exception as e:
        logger.error(f"Step '{step_name}' failed with unexpected error: {e}")
        return False


def verify_artifacts(expected_artifacts: Dict[str, str], base_path: Path) -> bool:
    """
    Verifies the existence of expected artifacts.

    Args:
        expected_artifacts: Dictionary mapping artifact type to relative path.
        base_path: Root directory to resolve paths against.

    Returns:
        True if all artifacts exist, False otherwise.
    """
    logger = get_logger()
    all_present = True

    for artifact_type, rel_path in expected_artifacts.items():
        full_path = base_path / rel_path
        if full_path.exists():
            logger.info(f"Artifact found: {artifact_type} ({rel_path})")
            # Optional: Check file size > 0 for non-empty validation
            if full_path.stat().st_size == 0:
                logger.warning(f"Artifact exists but is empty: {rel_path}")
                all_present = False
        else:
            logger.error(f"Missing artifact: {artifact_type} ({rel_path})")
            all_present = False

    return all_present


def validate_metrics_content(metrics_path: Path) -> bool:
    """
    Validates the content of the model metrics JSON file.

    Args:
        metrics_path: Path to the model_metrics.json file.

    Returns:
        True if the file contains expected keys and valid numeric values, False otherwise.
    """
    logger = get_logger()
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)

        required_keys = ['rf_r2', 'gb_r2', 'rf_mae', 'gb_mae', 'rf_rmse', 'gb_rmse']
        missing_keys = [k for k in required_keys if k not in data]

        if missing_keys:
            logger.error(f"Metrics file missing keys: {missing_keys}")
            return False

        # Check for numeric values
        for key in required_keys:
            val = data[key]
            if not isinstance(val, (int, float)):
                logger.error(f"Metric {key} is not numeric: {val}")
                return False

        logger.info("Metrics content validation passed.")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse metrics JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating metrics: {e}")
        return False


def main():
    """
    Main entry point for the quickstart validation script.
    Executes the pipeline and verifies outputs.
    """
    # Setup logging
    log_path = load_paths()['logs']
    logger = setup_logging(log_level=logging.INFO, log_file=log_path / 'quickstart_validation.log')
    logger.info("Starting Quickstart Validation (T052)...")

    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / 'code'
    data_dir = project_root / 'data'
    evaluation_dir = data_dir / 'evaluation'

    # Define expected artifacts based on the pipeline flow
    # Note: These paths assume the standard execution flow defined in tasks.md
    expected_artifacts = {
        "raw_dataset": "raw/mp-2020.12.1.csv",
        "filtered_dataset": "raw/mp-2020.12.1_filtered.csv",
        "processed_dataset": "processed/computed_descriptors.csv",
        "model_rf": "evaluation/model_rf.pkl",
        "model_gb": "evaluation/model_gb.pkl",
        "model_metrics": "evaluation/model_metrics.json",
        "feature_ranking": "evaluation/feature_ranking.json",
        "vif_scores": "evaluation/vif_scores.json",
        "ale_metrics": "evaluation/ale_metrics.json",
        "statistical_tests": "evaluation/statistical_tests.json"
    }

    # Define pipeline steps
    # We assume the pipeline is run via the main.py entry point or individual scripts
    # For robustness, we run the main pipeline script if it exists, otherwise individual steps.
    # Based on task T048a, main.py is the CLI entry point.
    pipeline_steps = [
        ("Data Ingestion & Descriptor Computation", [sys.executable, str(code_dir / 'main.py'), '--stage', 'ingest_descriptors']),
        ("Model Training & Evaluation", [sys.executable, str(code_dir / 'main.py'), '--stage', 'train_evaluate']),
        ("Feature Importance & Plotting", [sys.executable, str(code_dir / 'main.py'), '--stage', 'importance_plots'])
    ]

    # Fallback: If main.py doesn't support stages, try running individual scripts
    # This logic handles cases where the main.py might not be fully implemented yet
    # or if the user prefers running scripts directly.
    # We will attempt the main.py first.
    
    success = True

    # Check if main.py exists and supports the expected interface
    main_py = code_dir / 'main.py'
    if not main_py.exists():
        logger.error("code/main.py not found. Cannot run pipeline via CLI.")
        success = False
    else:
        # Attempt to run the pipeline
        # Note: We run them sequentially to ensure dependencies are met
        for step_name, command in pipeline_steps:
            if not run_step(step_name, command, cwd=project_root):
                logger.warning(f"Step '{step_name}' failed. Continuing to check artifacts...")
                # We do not fail immediately to allow artifact verification to report exactly what is missing
                success = False

    # Verify Artifacts
    logger.info("--- Verifying Artifacts ---")
    artifacts_ok = verify_artifacts(expected_artifacts, project_root)
    if not artifacts_ok:
        success = False

    # Validate Metrics Content
    if (project_root / expected_artifacts['model_metrics']).exists():
        logger.info("--- Validating Metrics Content ---")
        metrics_ok = validate_metrics_content(project_root / expected_artifacts['model_metrics'])
        if not metrics_ok:
            success = False
    else:
        logger.warning("Skipping metrics content validation: file not found.")

    # Final Report
    logger.info("--- Validation Summary ---")
    if success:
        logger.info("Quickstart Validation PASSED: All steps executed and artifacts verified.")
        sys.exit(0)
    else:
        logger.error("Quickstart Validation FAILED: Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
