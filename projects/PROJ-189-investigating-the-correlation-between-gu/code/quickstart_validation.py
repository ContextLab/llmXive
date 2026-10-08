"""
Quickstart Validation Script for PROJ-189
Validates end-to-end reproducibility by executing the pipeline steps
defined in quickstart.md and verifying the resulting artifacts.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROCESSED_DIR / "quickstart_validation.log")
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name: str, args: list = None) -> bool:
    """
    Execute a Python script in the code directory.
    Returns True if successful, False otherwise.
    """
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(CODE_DIR),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per script
        )

        if result.returncode != 0:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        logger.info(f"Script {script_name} completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running script {script_name}: {e}")
        return False

def verify_artifact(path_str: str, must_exist: bool = True, min_size_bytes: int = 0) -> bool:
    """
    Verify that an artifact exists and meets size requirements.
    Returns True if valid, False otherwise.
    """
    path = PROJECT_ROOT / path_str
    exists = path.exists()

    if must_exist and not exists:
        logger.error(f"Artifact missing: {path}")
        return False

    if must_exist and exists:
        size = path.stat().st_size
        if size < min_size_bytes:
            logger.error(f"Artifact {path} is too small ({size} bytes < {min_size_bytes})")
            return False
        logger.info(f"Artifact verified: {path} ({size} bytes)")
        return True

    return True

def verify_json_content(path_str: str, required_keys: list = None) -> bool:
    """
    Verify that a JSON file exists and contains required keys.
    Returns True if valid, False otherwise.
    """
    path = PROJECT_ROOT / path_str
    if not path.exists():
        logger.error(f"JSON artifact missing: {path}")
        return False

    try:
        with open(path, 'r') as f:
            data = json.load(f)

        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                logger.error(f"JSON {path} missing keys: {missing}")
                return False

        logger.info(f"JSON artifact verified: {path}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error verifying JSON {path}: {e}")
        return False

def main():
    logger.info("Starting Quickstart Validation for PROJ-189")
    start_time = datetime.now()

    # Define the validation steps based on the pipeline
    # Order matters: Data Ingestion -> Preprocessing -> Correlation -> Modeling -> Validation
    steps = [
        {
            "name": "Data Ingestion",
            "script": "01_data_ingestion.py",
            "artifacts": [
                ("data/processed/merged_data.parquet", 1024), # 1KB min
                ("data/processed/merge_log.json", 100)
            ]
        },
        {
            "name": "Preprocessing",
            "script": "02_preprocessing.py",
            "artifacts": [
                ("data/processed/rarefied_relative_abundance.parquet", 1024),
                ("data/processed/checksums.json", 100)
            ]
        },
        {
            "name": "Correlation Analysis",
            "script": "03_correlation_analysis.py",
            "artifacts": [
                ("data/processed/corpus_clr.parquet", 1024),
                ("data/processed/correlation_results.csv", 1024),
                ("data/processed/correlation_summary.json", 100)
            ]
        },
        {
            "name": "Predictive Modeling",
            "script": "04_predictive_modeling.py",
            "artifacts": [
                ("data/models/model.pkl", 1024),
                ("data/processed/significance_verification.json", 100),
                ("data/processed/null_threshold.json", 100),
                ("data/processed/top_taxa_final.json", 100),
                ("data/processed/memory_log.txt", 100)
            ]
        },
        {
            "name": "Sensitivity Analysis",
            "script": "05_sensitivity_analysis.py",
            "artifacts": [
                ("data/processed/sensitivity_variance_report.json", 100)
            ]
        }
    ]

    all_passed = True
    results = {
        "timestamp": start_time.isoformat(),
        "steps": [],
        "overall_status": "PASSED"
    }

    for step in steps:
        logger.info(f"--- Validating Step: {step['name']} ---")
        step_result = {
            "name": step["name"],
            "script": step["script"],
            "status": "PASSED",
            "artifacts": []
        }

        # Run the script
        if not run_script(step["script"]):
            step_result["status"] = "FAILED"
            all_passed = False
            logger.error(f"Step {step['name']} failed during execution.")
        else:
            # Verify artifacts
            for artifact_path, min_size in step["artifacts"]:
                is_valid = verify_artifact(artifact_path, must_exist=True, min_size_bytes=min_size)
                artifact_status = "PASS" if is_valid else "FAIL"
                if not is_valid:
                    all_passed = False
                    step_result["status"] = "FAILED"
                
                # Check if it's JSON and verify content if possible
                if artifact_path.endswith('.json'):
                    json_valid = verify_json_content(artifact_path)
                    if not json_valid:
                        all_passed = False
                        step_result["status"] = "FAILED"
                
                step_result["artifacts"].append({
                    "path": artifact_path,
                    "status": artifact_status
                })

        results["steps"].append(step_result)
        if step_result["status"] == "FAILED":
            logger.error(f"Step {step['name']} FAILED.")
        else:
            logger.info(f"Step {step['name']} PASSED.")

    # Final Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    results["duration_seconds"] = duration
    results["overall_status"] = "PASSED" if all_passed else "FAILED"

    # Save validation report
    report_path = PROCESSED_DIR / "quickstart_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Validation complete. Report saved to {report_path}")
    logger.info(f"Overall Status: {results['overall_status']}")
    logger.info(f"Total Duration: {duration:.2f} seconds")

    if not all_passed:
        logger.error("Quickstart validation FAILED. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Quickstart validation PASSED successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
