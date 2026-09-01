"""
Quickstart Validation Script for PROJ-295.

This script validates the end-to-end reproducibility of the pipeline by:
1. Verifying the existence of required configuration and data files.
2. Executing the main pipeline entry point (code/main.py).
3. Validating that expected output artifacts are generated.
4. Reporting pass/fail status with detailed logs.

Usage:
    python code/validate_quickstart.py
"""
import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUICKSTART_SCRIPT = PROJECT_ROOT / "code" / "main.py"
CONFIG_FILE = PROJECT_ROOT / "pipeline_config.yaml"
EXPECTED_OUTPUTS = [
    "results/model_metrics.json",
    "results/channel_importance.json",
    "results/sensitivity_report.csv"
]

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists at the given path."""
    if path.exists():
        logger.info(f"[PASS] {description} found: {path}")
        return True
    else:
        logger.error(f"[FAIL] {description} missing: {path}")
        return False

def validate_json_content(path: Path) -> bool:
    """Validate that a file contains valid JSON."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.info(f"[PASS] {path} contains valid JSON with keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"[FAIL] {path} contains invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Error reading {path}: {e}")
        return False

def validate_yaml_content(path: Path) -> bool:
    """Validate that a file contains valid YAML (basic check)."""
    import yaml
    try:
        with open(path, 'r') as f:
            yaml.safe_load(f)
        logger.info(f"[PASS] {path} contains valid YAML")
        return True
    except yaml.YAMLError as e:
        logger.error(f"[FAIL] {path} contains invalid YAML: {e}")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Error reading {path}: {e}")
        return False

def run_quickstart(args: argparse.Namespace) -> bool:
    """Execute the main pipeline script."""
    cmd = [
        sys.executable,
        str(QUICKSTART_SCRIPT),
        "--data-dir", str(args.data_dir),
        "--output-dir", str(args.output_dir)
    ]

    logger.info(f"Executing quickstart command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=args.timeout
        )

        if result.returncode == 0:
            logger.info("[PASS] Pipeline execution completed successfully.")
            return True
        else:
            logger.error(f"[FAIL] Pipeline execution failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"[FAIL] Pipeline execution timed out after {args.timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Error executing pipeline: {e}")
        return False

def verify_outputs(output_dir: Path) -> bool:
    """Verify that all expected output files exist and are valid."""
    all_valid = True
    for rel_path in EXPECTED_OUTPUTS:
        full_path = output_dir / rel_path
        if not full_path.exists():
            logger.error(f"[FAIL] Expected output missing: {full_path}")
            all_valid = False
            continue

        # Validate content based on extension
        if full_path.suffix == '.json':
            if not validate_json_content(full_path):
                all_valid = False
        elif full_path.suffix == '.csv':
            try:
                import pandas as pd
                df = pd.read_csv(full_path)
                logger.info(f"[PASS] {full_path} contains valid CSV with {len(df)} rows.")
            except Exception as e:
                logger.error(f"[FAIL] Error reading CSV {full_path}: {e}")
                all_valid = False
        else:
            logger.info(f"[INFO] Skipping validation for unknown format: {full_path}")

    return all_valid

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart reproducibility")
    parser.add_argument("--data-dir", type=str, default="data/processed",
                        help="Path to processed data directory")
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Path to output directory")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Timeout in seconds for pipeline execution")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation for PROJ-295")
    logger.info("=" * 60)

    # 1. Check prerequisites
    prerequisites_ok = True
    if not check_file_exists(CONFIG_FILE, "Pipeline Configuration"):
        prerequisites_ok = False
    if not check_file_exists(QUICKSTART_SCRIPT, "Main Pipeline Script"):
        prerequisites_ok = False

    if not prerequisites_ok:
        logger.error("Prerequisites check failed. Aborting validation.")
        sys.exit(1)

    # 2. Run the pipeline
    execution_ok = run_quickstart(args)

    # 3. Verify outputs
    output_dir = PROJECT_ROOT / args.output_dir
    output_ok = False
    if execution_ok:
        logger.info("Verifying output artifacts...")
        output_ok = verify_outputs(output_dir)
    else:
        logger.warning("Skipping output verification due to execution failure.")

    # 4. Final Report
    logger.info("=" * 60)
    if execution_ok and output_ok:
        logger.info("VALIDATION RESULT: PASSED")
        logger.info("End-to-end reproducibility confirmed.")
        # Write a summary report
        report_path = output_dir / "quickstart_validation_report.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "passed",
            "prerequisites": "ok",
            "execution": "ok",
            "outputs": "ok",
            "command": f"python {QUICKSTART_SCRIPT} --data-dir {args.data_dir} --output-dir {args.output_dir}"
        }
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Validation report saved to: {report_path}")
        sys.exit(0)
    else:
        logger.error("VALIDATION RESULT: FAILED")
        if not execution_ok:
            logger.error("Reason: Pipeline execution failed.")
        elif not output_ok:
            logger.error("Reason: Expected output artifacts missing or invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
