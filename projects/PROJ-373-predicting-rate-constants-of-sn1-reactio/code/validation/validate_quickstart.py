"""
T034: Validate quickstart.md against actual execution.

This script executes the pipeline steps described in specs/001-predict-sn1-rate-constants/quickstart.md
and verifies that all expected artifacts are generated.
"""
import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logging, get_logger
from config import ensure_dirs

# Setup logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"quickstart_validation_{timestamp}.log"
logger = setup_logging(level=logging.INFO, log_file=log_file)

def run_command(cmd, cwd=None, description=""):
    """Run a shell command and return success status."""
    logger.info(f"Executing: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per step
        )
        
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully")
            if result.stdout:
                logger.debug(f"stdout: {result.stdout[:500]}")
            return True
        else:
            logger.error(f"✗ {description} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"stderr: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {description} timed out")
        return False
    except Exception as e:
        logger.error(f"✗ {description} raised exception: {e}")
        return False

def verify_artifact(path, description):
    """Verify an artifact exists and is non-empty."""
    full_path = PROJECT_ROOT / path
    if full_path.exists():
        size = full_path.stat().st_size
        if size > 0:
            logger.info(f"✓ {description} exists ({size} bytes)")
            return True
        else:
            logger.error(f"✗ {description} exists but is empty")
            return False
    else:
        logger.error(f"✗ {description} not found at {full_path}")
        return False

def main():
    """Execute quickstart validation."""
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation")
    logger.info("=" * 60)
    
    ensure_dirs()
    
    all_passed = True
    
    # Step 1: Data Ingestion and Preprocessing
    logger.info("\n--- Step 1: Data Ingestion and Preprocessing ---")
    step1 = run_command(
        [sys.executable, "code/data/ingest.py"],
        description="Data ingestion"
    )
    step1 = step1 and run_command(
        [sys.executable, "code/data/clean.py"],
        description="Data cleaning"
    )
    step1 = step1 and run_command(
        [sys.executable, "code/data/descriptors.py"],
        description="Descriptor calculation"
    )
    step1 = step1 and run_command(
        [sys.executable, "code/data/split.py"],
        description="Data splitting"
    )
    
    if not step1:
        logger.error("Data preprocessing step failed")
        all_passed = False
    else:
        # Verify preprocessing artifacts
        verify_artifact("data/processed/cleaned_sn1.csv", "Cleaned dataset")
        verify_artifact("data/processed/exclusion_report.csv", "Exclusion report")
        
    # Step 2: Model Training
    logger.info("\n--- Step 2: Model Training ---")
    step2 = run_command(
        [sys.executable, "code/models/train.py"],
        description="Model training with hyperparameter search"
    )
    
    if not step2:
        logger.error("Model training failed")
        all_passed = False
    else:
        verify_artifact("artifacts/best_model.pt", "Best model weights")
        verify_artifact("artifacts/metrics.json", "Model metrics")
        verify_artifact("artifacts/hyperparameter_search.log", "Hyperparameter log")
        
    # Step 3: Evaluation and Interpretability
    logger.info("\n--- Step 3: Evaluation and Interpretability ---")
    step3 = run_command(
        [sys.executable, "code/models/evaluate.py"],
        description="Model evaluation"
    )
    step3 = step3 and run_command(
        [sys.executable, "code/analysis/interpret.py"],
        description="SHAP analysis and perturbation study"
    )
    step3 = step3 and run_command(
        [sys.executable, "code/analysis/sensitivity.py"],
        description="Sensitivity analysis"
    )
    step3 = step3 and run_command(
        [sys.executable, "code/analysis/collinearity.py"],
        description="Collinearity analysis"
    )
    step3 = step3 and run_command(
        [sys.executable, "code/analysis/power.py"],
        description="Power analysis"
    )
    
    if not step3:
        logger.error("Analysis step failed")
        all_passed = False
    else:
        verify_artifact("artifacts/feature_importance.png", "Feature importance plot")
        verify_artifact("artifacts/sensitivity_report.csv", "Sensitivity report")
        verify_artifact("artifacts/perturbation_results.csv", "Perturbation results")
        verify_artifact("artifacts/power_analysis_report.csv", "Power analysis report")
        
    # Final summary
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✓ ALL VALIDATION STEPS PASSED")
        logger.info("quickstart.md has been successfully validated against actual execution")
    else:
        logger.error("✗ VALIDATION FAILED")
        logger.error("Some steps did not complete successfully")
    logger.info("=" * 60)
    
    # Write summary report
    summary_path = PROJECT_ROOT / "artifacts" / "quickstart_validation_summary.txt"
    with open(summary_path, "w") as f:
        f.write(f"Quickstart Validation Summary\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: {'PASSED' if all_passed else 'FAILED'}\n")
        f.write(f"Log file: {log_file}\n")
    
    logger.info(f"Summary written to: {summary_path}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())