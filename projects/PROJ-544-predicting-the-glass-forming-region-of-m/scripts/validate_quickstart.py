"""
T034: Validate quickstart
Runs the CI validation script end-to-end and logs the result.
"""
import subprocess
import sys
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "quickstart_validation.log"

# Set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Quickstart Validation (T034)")
    logger.info("Running scripts/run-ci.sh --dry-run")

    script_path = Path("scripts/run-ci.sh")
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        logger.error("Validation FAILED: run-ci.sh missing")
        return 1

    try:
        # Execute the CI script
        # Using shell=True to handle the script execution correctly on Unix-like systems
        # and to capture the exit code properly.
        result = subprocess.run(
            ["bash", str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        logger.info(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            logger.info("STDOUT:\n" + result.stdout)
        if result.stderr:
            logger.info("STDERR:\n" + result.stderr)

        if result.returncode == 0:
            logger.info("SUCCESS: scripts/run-ci.sh exited with code 0")
            logger.info("Quickstart validation PASSED")
            return 0
        else:
            logger.error(f"FAILURE: scripts/run-ci.sh exited with code {result.returncode}")
            logger.error("Quickstart validation FAILED")
            return 1

    except subprocess.TimeoutExpired:
        logger.error("FAILURE: scripts/run-ci.sh timed out after 300 seconds")
        logger.error("Quickstart validation FAILED")
        return 1
    except Exception as e:
        logger.error(f"FAILURE: Exception occurred during execution: {str(e)}")
        logger.error("Quickstart validation FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
