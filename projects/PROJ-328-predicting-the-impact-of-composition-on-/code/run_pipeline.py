import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import subprocess

from utils.logging_config import get_logger
from seed import init_reproducibility

logger = get_logger(__name__)

def run_step(command: str, step_name: str) -> bool:
    """Runs a single pipeline step command."""
    logger.info(f"Running step: {step_name}")
    logger.info(f"Command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.debug(result.stdout)
        if result.stderr:
            logger.debug(result.stderr)
        logger.info(f"Step {step_name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step {step_name} failed with return code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False

def verify_deliverables(deliverables: List[str]) -> bool:
    """Verifies that all expected deliverable files exist."""
    all_exist = True
    for file_path in deliverables:
        if not Path(file_path).exists():
            logger.error(f"Deliverable missing: {file_path}")
            all_exist = False
        else:
            logger.info(f"Deliverable found: {file_path}")
    return all_exist

def main():
    """
    Orchestrates the execution of the research pipeline.
    """
    init_reproducibility()
    
    # Define the sequence of steps based on the task dependencies
    # Phase 1: Setup (Already done, but directories might need verification)
    # Phase 2: Foundation (Already done)
    
    # Phase 3: User Story 1 (Ingestion)
    # T012d-Execute (Literature Scraper)
    # T013 (Cleaner)
    # T014 (Validator) - produces .ingestion_status.json
    
    # Phase 4: User Story 2 (Features & Models)
    # T023b (CLR Transform) - produces clr_features.csv
    # T023c (Descriptors) - produces descriptors.csv
    # T024 (VIF)
    # T025 (XGBoost)
    # T026 (Linear)
    # ... (remaining steps)

    steps = [
        # Ingestion Phase
        ("python code/ingestion/literature_scraper.py", "T012d-Execute: Literature Scraper"),
        ("python code/ingestion/cleaner.py", "T013: Data Cleaner"),
        ("python code/ingestion/validator.py", "T014: Data Validator"),
        
        # Feature Engineering Phase (T023b is the focus of this task)
        ("python code/features/descriptor_engine.py", "T023b/T023c: CLR Transform & Physical Descriptors"),
        
        # Collinearity
        ("python code/features/collinearity.py", "T024: VIF Calculation"),
        
        # Model Training
        ("python code/models/xgboost_trainer.py", "T025: XGBoost Training"),
        ("python code/models/linear_trainer.py", "T026: Linear Regression Training"),
        
        # Evaluation
        ("python code/evaluation/cv.py", "T027: Cross-Validation"),
        ("python code/evaluation/bootstrap.py", "T028/T029b: Bootstrap Metrics"),
        ("python code/evaluation/sensitivity.py", "T029c: Sensitivity Analysis"),
        ("python code/evaluation/shap_analysis.py", "T030: SHAP Analysis"),
        
        # Reporting
        ("python code/evaluation/generate_report.py", "T031c: Report Generation"),
    ]

    failed_steps = []
    
    for cmd, name in steps:
        if not run_step(cmd, name):
            failed_steps.append(name)
            # Depending on strictness, we might stop here. For now, continue to see other failures.
            # But critical path failures should probably stop.
            if "T013" in name or "T023b" in name or "T025" in name:
                logger.critical(f"Critical step {name} failed. Stopping pipeline.")
                break

    if failed_steps:
        logger.error(f"Pipeline failed. Failed steps: {failed_steps}")
        sys.exit(1)

    # Verify critical deliverables
    deliverables = [
        "data/processed/.ingestion_status.json",
        "data/processed/clr_features.csv",
        "data/processed/descriptors.csv",
        "data/processed/report.yaml"
    ]

    if not verify_deliverables(deliverables):
        logger.error("Pipeline finished but critical deliverables are missing.")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()