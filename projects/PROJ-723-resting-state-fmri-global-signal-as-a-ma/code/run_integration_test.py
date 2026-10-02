"""
End-to-End Integration Test for the Resting-State fMRI Global Signal Pipeline.

This script executes the full pipeline on a sample data subset to verify
that all components (Ingestion, Modeling, Robustness, Visualizations, Reporting)
function correctly together and produce the required artifacts.

It validates:
1. Directory structure creation.
2. Data ingestion and cleaning (T016).
3. Model training and null distribution generation (T019, T021).
4. Robustness analysis (T031).
5. Visualization generation (T035).
6. Final report generation with criteria status (T034b).
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import project modules using the verified API surface
from config import ensure_directories
from utils import get_logger, read_json, write_json, file_exists
from ingestion import main as run_ingestion_main
from modeling import main as run_modeling_main
from robustness import main as run_robustness_main
from visualizations import main as run_visualizations_main
from run_final_report import main as run_final_report_main

# Configure logging for the integration test
logger = get_logger("integration_test")

def check_file_exists(path_str: str, description: str) -> bool:
    """Check if a required file exists."""
    path = Path(path_str)
    exists = path.exists()
    if exists and path.stat().st_size == 0:
        logger.error(f"File exists but is empty: {path_str} ({description})")
        return False
    if not exists:
        logger.error(f"File missing: {path_str} ({description})")
    else:
        logger.info(f"Verified: {path_str} ({description})")
    return exists

def run_step(step_name: str, func, *args, **kwargs) -> Tuple[bool, str]:
    """Execute a pipeline step and handle errors."""
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"--- Completed Step: {step_name} in {elapsed:.2f}s ---")
        return True, f"Success ({elapsed:.2f}s)"
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- FAILED Step: {step_name} after {elapsed:.2f}s ---")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False, f"Failed: {str(e)}"

def run_ingestion() -> Tuple[bool, str]:
    """Run the ingestion pipeline (T016)."""
    # The ingestion main function handles its own logic
    # We wrap it to ensure it runs in the integration context
    try:
        # Ensure we are running the ingestion logic
        # Note: ingestion.py main() expects to be run as a script or called carefully
        # We assume the environment is set up correctly by T004 (config)
        run_ingestion_main()
        return True, "Ingestion completed"
    except Exception as e:
        raise RuntimeError(f"Ingestion failed: {e}")

def run_modeling() -> Tuple[bool, str]:
    """Run the modeling pipeline (T019, T021, T025)."""
    try:
        run_modeling_main()
        return True, "Modeling completed"
    except Exception as e:
        raise RuntimeError(f"Modeling failed: {e}")

def run_robustness() -> Tuple[bool, str]:
    """Run the robustness analysis (T031)."""
    try:
        run_robustness_main()
        return True, "Robustness completed"
    except Exception as e:
        raise RuntimeError(f"Robustness failed: {e}")

def run_visualizations() -> Tuple[bool, str]:
    """Run visualization generation (T035)."""
    try:
        run_visualizations_main()
        return True, "Visualizations completed"
    except Exception as e:
        raise RuntimeError(f"Visualizations failed: {e}")

def run_final_report() -> Tuple[bool, str]:
    """Run the final report generation (T034a, T034b)."""
    try:
        run_final_report_main()
        return True, "Final Report completed"
    except Exception as e:
        raise RuntimeError(f"Final Report failed: {e}")

def validate_artifacts() -> bool:
    """Validate that all required output artifacts exist and are non-empty."""
    required_files = [
        ("data/processed/cleaned_data.csv", "Cleaned Data"),
        ("data/results/full_model.json", "Full Model Results"),
        ("data/results/null_distribution.json", "Null Distribution"),
        ("data/results/delta_r2.json", "Delta R2"),
        ("data/results/robustness_report.json", "Robustness Report"),
        ("data/results/diagnostics.json", "Diagnostics"),
        ("data/results/model_report.json", "Model Report"),
        ("data/results/final_report.json", "Final Report"),
        ("data/results/null_dist.png", "Null Distribution Plot"),
        ("data/results/alpha_sweep.png", "Alpha Sweep Plot"),
        ("data/results/corr_matrix.png", "Correlation Matrix Plot"),
    ]

    all_valid = True
    for path, desc in required_files:
        if not check_file_exists(path, desc):
            all_valid = False

    # Specific validation for T034b: criteria_status in final_report.json
    final_report_path = "data/results/final_report.json"
    if file_exists(final_report_path):
        try:
            report = read_json(final_report_path)
            if "criteria_status" not in report:
                logger.error("FINAL REPORT MISSING 'criteria_status' OBJECT")
                all_valid = False
            else:
                logger.info("Verified 'criteria_status' object in final_report.json")
                # Check for SC-001 to SC-005
                for i in range(1, 6):
                    key = f"SC-00{i}"
                    if key not in report["criteria_status"]:
                        logger.warning(f"Missing criteria {key} in final_report.json")
                    else:
                        entry = report["criteria_status"][key]
                        if "status" not in entry or "narrative_summary" not in entry or "metrics" not in entry:
                            logger.warning(f"Invalid structure for {key} in final_report.json")
        except Exception as e:
            logger.error(f"Could not parse final_report.json: {e}")
            all_valid = False

    return all_valid

def main():
    """Main entry point for the integration test."""
    logger.info("=" * 60)
    logger.info("STARTING END-TO-END INTEGRATION TEST (T036)")
    logger.info("=" * 60)

    # 1. Setup
    ensure_directories()
    logger.info("Directories ensured.")

    # 2. Run Pipeline Steps
    steps = [
        ("Ingestion", run_ingestion),
        ("Modeling", run_modeling),
        ("Robustness", run_robustness),
        ("Visualizations", run_visualizations),
        ("Final Report", run_final_report),
    ]

    pipeline_success = True
    for name, func in steps:
        success, msg = run_step(name, func)
        if not success:
            pipeline_success = False
            logger.error(f"Pipeline halted at {name}: {msg}")
            break

    if not pipeline_success:
        logger.error("Integration Test FAILED due to pipeline execution error.")
        sys.exit(1)

    # 3. Validate Artifacts
    logger.info("Validating output artifacts...")
    if not validate_artifacts():
        logger.error("Integration Test FAILED: Missing or invalid artifacts.")
        sys.exit(1)

    # 4. Summary
    logger.info("=" * 60)
    logger.info("INTEGRATION TEST PASSED")
    logger.info("All pipeline steps executed successfully.")
    logger.info("All required artifacts generated and validated.")
    logger.info("T036: End-to-End Integration Test Complete.")
    logger.info("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
