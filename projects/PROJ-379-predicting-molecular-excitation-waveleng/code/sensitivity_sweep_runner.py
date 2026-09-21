"""
Runner script for T042: Execute sensitivity analysis and verify outputs.
This script orchestrates the execution of sensitivity.py and verifies the outputs.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("t042_runner")

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

def verify_output_file(path: Path, required_keys: list = None) -> bool:
    """Verify that an output file exists and contains expected content."""
    if not path.exists():
        logger.error(f"Output file missing: {path}")
        return False
    
    logger.info(f"Verifying output: {path}")
    
    if path.suffix == '.json':
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if required_keys:
                for key in required_keys:
                    if key not in data:
                        logger.error(f"Missing key '{key}' in {path}")
                        return False
            logger.info(f"Valid JSON with {len(data) if isinstance(data, (list, dict)) else 'scalar'} entries")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            return False
    elif path.suffix == '.csv':
        import pandas as pd
        try:
            df = pd.read_csv(path)
            logger.info(f"Valid CSV with {len(df)} rows, columns: {list(df.columns)}")
            return True
        except Exception as e:
            logger.error(f"Invalid CSV in {path}: {e}")
            return False
    else:
        # Generic file check
        if path.stat().st_size > 0:
            logger.info(f"File exists and is non-empty: {path}")
            return True
        else:
            logger.error(f"File is empty: {path}")
            return False

def main():
    logger.info("Starting T042 Execution: Explain and Sensitivity Analysis")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    data_dir = project_root / "data" / "processed"
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check prerequisites
    required_files = [
        "data/processed/model.pt",
        "data/processed/test.csv",
        "data/processed/predictions.csv"
    ]
    
    for req_file in required_files:
        if not (project_root / req_file).exists():
            logger.error(f"Prerequisite missing: {req_file}")
            logger.error("Please run previous tasks (T040, T041) first.")
            sys.exit(1)
    
    # Step 1: Run explain.py
    explain_cmd = [
        sys.executable,
        str(code_dir / "explain.py"),
        "--model", str(data_dir / "model.pt"),
        "--data", str(data_dir / "test.csv"),
        "--output", str(data_dir / "raw_attribution.json"),
        "--masked-output", str(data_dir / "masked_attribution.json")
    ]
    
    if not run_command(explain_cmd, "Running explain.py"):
        logger.error("explain.py failed. Aborting.")
        sys.exit(1)
    
    # Verify explain outputs
    explain_outputs = [
        (data_dir / "raw_attribution.json", None),
        (data_dir / "masked_attribution.json", None)
    ]
    
    explain_success = True
    for path, keys in explain_outputs:
        if not verify_output_file(path, keys):
            explain_success = False
    
    if not explain_success:
        logger.error("Explain output verification failed.")
        sys.exit(1)
    
    # Step 2: Run sensitivity.py
    sensitivity_cmd = [
        sys.executable,
        str(code_dir / "sensitivity.py"),
        "--predictions", str(data_dir / "predictions.csv"),
        "--output", str(data_dir / "sensitivity_report.csv"),
        "--thresholds", "15,30,45,50"
    ]
    
    if not run_command(sensitivity_cmd, "Running sensitivity.py"):
        logger.error("sensitivity.py failed. Aborting.")
        sys.exit(1)
    
    # Verify sensitivity outputs
    sensitivity_outputs = [
        (data_dir / "sensitivity_report.csv", None),
        (data_dir / "sensitivity_report.md", None)  # Optional but expected by T026b
    ]
    
    sensitivity_success = True
    for path, keys in sensitivity_outputs:
        if not verify_output_file(path, keys):
            # Only fail if CSV is missing; MD is optional
            if path.suffix == '.csv':
                sensitivity_success = False
            else:
                logger.warning(f"Optional output missing: {path}")
    
    if not sensitivity_success:
        logger.error("Sensitivity output verification failed.")
        sys.exit(1)
    
    # Step 3: Generate summary report
    summary = {
        "task_id": "T042",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "artifacts_generated": [
          "data/processed/raw_attribution.json",
          "data/processed/masked_attribution.json",
          "data/processed/sensitivity_report.csv"
        ],
        "checks_passed": {
            "explain_execution": True,
            "explain_output": explain_success,
            "sensitivity_execution": True,
            "sensitivity_output": sensitivity_success
        }
    }
    
    summary_path = data_dir / "t042_execution_log.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Execution summary saved to {summary_path}")
    logger.info("T042 Execution completed successfully.")

if __name__ == "__main__":
    main()