"""
T039: Quickstart Validation Script
Runs the full pipeline to ensure reproducibility as defined in quickstart.md.
Verifies that all expected artifacts are generated and valid.
"""
import os
import sys
import json
import logging
import subprocess
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models" / "artifacts"
RESULTS_REPORTS = PROJECT_ROOT / "results" / "reports"
RESULTS_PLOTS = PROJECT_ROOT / "results" / "plots"
STATE_FILE = PROJECT_ROOT / "state.yaml"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def run_script(script_name: str, description: str) -> bool:
    """Run a pipeline script and return True if successful."""
    script_path = PROJECT_ROOT / "code" / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    logger.info(f"Running: {description} ({script_name})")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed with code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False
        logger.info(f"Script {script_name} completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"Verified: {description} exists at {path}")
        return True
    else:
        logger.error(f"Missing: {description} at {path}")
        return False

def check_file_not_empty(path: Path, description: str) -> bool:
    """Check if a file exists and is not empty."""
    if not check_file_exists(path, description):
        return False
    if path.stat().st_size == 0:
        logger.error(f"Empty: {description} at {path}")
        return False
    logger.info(f"Verified: {description} is not empty")
    return True

def validate_json_structure(path: Path, required_keys: list) -> bool:
    """Validate a JSON file has the required structure."""
    if not check_file_exists(path, f"JSON report {path.name}"):
        return False
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            logger.error(f"Missing keys in {path}: {missing}")
            return False
        logger.info(f"Verified: {path.name} has required keys {required_keys}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return False

def validate_yaml_structure(path: Path) -> bool:
    """Validate state.yaml exists and is not empty."""
    return check_file_not_empty(path, "state.yaml")

def main():
    logger.info("Starting Quickstart Validation (T039)...")
    all_passed = True

    # 1. Verify Prerequisites (Contracts)
    logger.info("\n--- Checking Prerequisites ---")
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    if not check_file_exists(schema_path, "Dataset Schema"):
        all_passed = False
        # If schema is missing, we can't proceed with validation logic, but we try to run download/preprocess
        # as they might create it or fail gracefully. However, task T004 says it should exist.
        logger.warning("Schema missing. Pipeline steps depending on it may fail.")

    # 2. Run Data Acquisition (T012, T013)
    logger.info("\n--- Running Data Acquisition ---")
    if not run_script("download_data.py", "Download Data"):
        all_passed = False
    else:
        # Check raw data
        raw_files = list(DATA_RAW.glob("*.csv"))
        if not raw_files:
            logger.error("No raw CSV files found after download.")
            all_passed = False
        else:
            logger.info(f"Found raw data files: {[f.name for f in raw_files]}")

    # 3. Run Preprocessing (T014-T018)
    logger.info("\n--- Running Preprocessing ---")
    if not run_script("preprocess.py", "Preprocess Data"):
        all_passed = False
    else:
        cleaned_path = DATA_PROCESSED / "cleaned_316L.csv"
        if not check_file_not_empty(cleaned_path, "Cleaned Dataset"):
            all_passed = False

    # 4. Run Model Training (T021-T027)
    logger.info("\n--- Running Model Training ---")
    if not run_script("train_models.py", "Train Models"):
        all_passed = False
    else:
        # Check model artifacts
        models = list(MODELS_DIR.glob("*.pkl"))
        if len(models) < 2:
            logger.error(f"Expected at least 2 model files, found {len(models)}")
            all_passed = False
        else:
            logger.info(f"Found model files: {[m.name for m in models]}")

        # Check metrics report
        metrics_path = RESULTS_REPORTS / "model_metrics.json"
        if not validate_json_structure(metrics_path, ["gb_metrics", "mlp_metrics", "dummy_baseline"]):
            all_passed = False

    # 5. Run Explainability (T030-T036)
    logger.info("\n--- Running Explainability Analysis ---")
    if not run_script("analyze_explainability.py", "Analyze Explainability"):
        all_passed = False
    else:
        # Check SHAP plot
        shap_plot = RESULTS_PLOTS / "shap_summary.png"
        if not check_file_not_empty(shap_plot, "SHAP Summary Plot"):
            all_passed = False

        # Check significance report
        sig_report = RESULTS_REPORTS / "significance_report.json"
        if not validate_json_structure(sig_report, ["features", "p_values", "significant_features"]):
            all_passed = False

    # 6. Verify State File
    logger.info("\n--- Verifying State File ---")
    if not validate_yaml_structure(STATE_FILE):
        all_passed = False

    # Final Summary
    logger.info("\n" + "="*50)
    if all_passed:
        logger.info("VALIDATION SUCCESSFUL: All artifacts generated and verified.")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED: One or more artifacts missing or invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()