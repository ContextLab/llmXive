import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

# Expected artifacts based on tasks.md and quickstart.md workflow
EXPECTED_ARTIFACTS = {
    "data/processed/hea_descriptors.csv": "Processed dataset with descriptors",
    "output/data_status.json": "Data status and count information",
    "output/metrics.json": "Model performance metrics (R2, MAE, RMSE)",
    "output/power_analysis.json": "Power analysis results",
    "output/report.md": "Final statistical report with disclaimers",
}

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists and log the result."""
    if os.path.exists(path):
        logger.info(f"[OK] Found: {path} ({description})")
        return True
    else:
        logger.error(f"[MISSING] Expected: {path} ({description})")
        return False

def check_quickstart_references(quickstart_path: str = "quickstart.md") -> bool:
    """Verify that quickstart.md exists and contains expected pipeline steps."""
    if not os.path.exists(quickstart_path):
        logger.error(f"[MISSING] quickstart.md not found at {quickstart_path}")
        return False

    with open(quickstart_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_steps = [
        "python code/data/pipeline.py",
        "python code/models/train.py",
        "python code/models/evaluate.py",
    ]

    missing_steps = []
    for step in required_steps:
        if step not in content:
            missing_steps.append(step)

    if missing_steps:
        logger.error(f"[FAIL] quickstart.md missing commands: {missing_steps}")
        return False

    logger.info("[OK] quickstart.md contains all required pipeline commands")
    return True

def validate_output_artifacts() -> bool:
    """Validate that all expected output artifacts exist."""
    logger.info("Validating output artifacts...")
    all_present = True
    for path, desc in EXPECTED_ARTIFACTS.items():
        if not check_file_exists(path, desc):
            all_present = False
    return all_present

def run_pipeline_validation() -> bool:
    """
    Attempt to run the quickstart steps to ensure they execute without error.
    This validates the actual code, not just the existence of files.
    """
    logger.info("Running pipeline validation steps...")
    
    # Step 1: Run Pipeline (Data Processing)
    logger.info("Step 1: Running data pipeline...")
    try:
        result = subprocess.run(
            [sys.executable, "code/data/pipeline.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        if result.returncode != 0:
            logger.error(f"[FAIL] Pipeline failed: {result.stderr}")
            return False
        logger.info("[OK] Pipeline executed successfully")
    except subprocess.TimeoutExpired:
        logger.error("[FAIL] Pipeline timed out")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Pipeline execution error: {str(e)}")
        return False

    # Step 2: Run Training
    logger.info("Step 2: Running model training...")
    try:
        result = subprocess.run(
            [sys.executable, "code/models/train.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        if result.returncode != 0:
            logger.error(f"[FAIL] Training failed: {result.stderr}")
            return False
        logger.info("[OK] Training executed successfully")
    except subprocess.TimeoutExpired:
        logger.error("[FAIL] Training timed out")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Training execution error: {str(e)}")
        return False

    # Step 3: Run Evaluation
    logger.info("Step 3: Running evaluation...")
    try:
        result = subprocess.run(
            [sys.executable, "code/models/evaluate.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        if result.returncode != 0:
            logger.error(f"[FAIL] Evaluation failed: {result.stderr}")
            return False
        logger.info("[OK] Evaluation executed successfully")
    except subprocess.TimeoutExpired:
        logger.error("[FAIL] Evaluation timed out")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Evaluation execution error: {str(e)}")
        return False

    return True

def main():
    """Main entry point for quickstart validation."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart.md Validation (Task T036)")
    logger.info("=" * 60)

    success = True

    # 1. Check quickstart.md existence and content
    if not check_quickstart_references():
        success = False

    # 2. Run the pipeline steps to verify they work
    if not run_pipeline_validation():
        success = False

    # 3. Validate output artifacts
    if not validate_output_artifacts():
        success = False

    # 4. Generate validation report
    report_path = "output/quickstart_validation_report.json"
    report = {
        "task_id": "T036",
        "status": "passed" if success else "failed",
        "timestamp": str(Path(report_path).stat().st_mtime if os.path.exists(report_path) else "now"),
        "checks": {
            "quickstart_exists": os.path.exists("quickstart.md"),
            "quickstart_commands_valid": success, # Derived from run_pipeline_validation
            "artifacts_present": success # Derived from validate_output_artifacts
        }
    }

    os.makedirs("output", exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to: {report_path}")

    if success:
        logger.info("=" * 60)
        logger.info("VALIDATION PASSED: Quickstart.md is valid and functional.")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("VALIDATION FAILED: See logs above for details.")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())