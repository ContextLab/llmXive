import os
import sys
import subprocess
import json
from pathlib import Path
import logging

# Add project root to path if needed, though running from root usually suffices
# Ensure we are running from the project root
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)

# Setup logging to file and console
log_path = project_root / "data" / "results" / "lint_report.txt"
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and log the result."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            # Stderr often contains formatting info from black/ruff, log as info
            logger.info(result.stderr)
        
        if result.returncode == 0:
            logger.info(f"Success: {description} completed without errors.")
            return True
        else:
            logger.error(f"Failure: {description} failed with exit code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout: {description} timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("Starting Linting and Formatting Pipeline (Task T039)")
    logger.info("=" * 60)

    code_dir = project_root / "code"
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    # 1. Run Ruff Check and Fix
    # ruff check code/ --fix
    ruff_success = run_command(
        ["ruff", "check", str(code_dir), "--fix"],
        "Ruff Check and Fix"
    )

    # 2. Run Black Format
    # black code/
    black_success = run_command(
        ["black", str(code_dir)],
        "Black Format"
    )

    # Final Status
    logger.info("=" * 60)
    if ruff_success and black_success:
        logger.info("Pipeline Status: SUCCESS")
        logger.info("All files have been linted and formatted successfully.")
        return 0
    else:
        logger.error("Pipeline Status: FAILED")
        logger.error("One or more steps failed. Check the log for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
