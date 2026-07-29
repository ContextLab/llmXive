import os
import sys
import subprocess
import json
from pathlib import Path
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("quickstart_validation")

def run_command(cmd: list, cwd: str = None) -> tuple:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return -1, "", str(e)

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists and is not empty."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File missing: {file_path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"File empty: {file_path}")
        return False
    logger.info(f"File verified: {file_path}")
    return True

def check_dependency_files() -> bool:
    """
    Pre-flight check: Assert dependency files exist.
    Dependencies:
      - T009: contracts/dataset.schema.yaml
      - T013a: code/data/synthetic_generator.py
      - T014: code/data/aggregation.py
    """
    deps = [
        "contracts/dataset.schema.yaml",
        "code/data/synthetic_generator.py",
        "code/data/aggregation.py"
    ]
    for dep in deps:
        if not check_file_exists(dep):
            logger.error(f"Dependency check failed: {dep}")
            return False
    logger.info("All dependency files present.")
    return True

def main():
    """
    Run quickstart.md validation:
    1. Pre-flight dependency checks.
    2. Execute bash quickstart.sh.
    3. Assert exit code 0.
    4. Verify data/processed/merged_data.csv exists.
    """
    logger.info("Starting Quickstart Validation (T038)")

    # 1. Pre-flight checks
    if not check_dependency_files():
        logger.critical("Pre-flight dependency check failed. Aborting.")
        sys.exit(1)

    # 2. Execute quickstart.sh
    quickstart_path = "quickstart.sh"
    if not check_file_exists(quickstart_path):
        logger.critical(f"Quickstart script not found: {quickstart_path}")
        sys.exit(1)

    exit_code, stdout, stderr = run_command(["bash", quickstart_path])

    # 3. Assert exit code 0
    if exit_code != 0:
        logger.error(f"Quickstart execution failed with exit code {exit_code}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        sys.exit(1)

    logger.info("Quickstart execution successful (exit code 0).")

    # 4. Verify declared deliverables
    required_files = [
        "data/processed/merged_data.csv",
        "data/processed/psychometrics.json",
        "data/raw/synthetic_data.csv",
        "data/raw/synthetic_data_marker.json"
    ]

    all_present = True
    for f in required_files:
        if not check_file_exists(f):
            all_present = False

    if not all_present:
        logger.critical("One or more required deliverables are missing after execution.")
        sys.exit(1)

    logger.info("All validation checks passed. T038 Complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())