"""
Pipeline Gate: Validates citations before allowing the main pipeline to proceed.

This script acts as the first step in the pipeline execution order.
It invokes the citation validator (T007a) and aborts the pipeline if validation fails.

Dependency: T007a (validate_citations.py)
"""
import os
import sys
import subprocess
import logging
from datetime import datetime

# Add project root to path to ensure imports work if run from subdirectories
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import setup_logging, get_logger, set_task_id, get_task_id

TASK_ID = "T007b"
GATE_SCRIPT = os.path.join(project_root, "code", "validate_citations.py")
LOG_DIR = os.path.join(project_root, "logs")
GATE_LOG_FILE = os.path.join(LOG_DIR, "pipeline_gate.log")

def ensure_log_dir():
    """Ensure the logs directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_failure(reason: str, logger: logging.Logger):
    """Log the specific validation failure reason to the gate log file."""
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [T007b] FAILURE: {reason}\n"
    
    # Append to the specific gate log file
    with open(GATE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.error(log_entry.strip())

def run_pipeline_gate():
    """
    Invokes the citation validator.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    setup_logging(task_id=TASK_ID)
    logger = get_logger(TASK_ID)
    set_task_id(TASK_ID)

    logger.info(f"Starting pipeline gate check (Task: {TASK_ID})")
    logger.info(f"Target script: {GATE_SCRIPT}")

    if not os.path.exists(GATE_SCRIPT):
        error_msg = f"Critical: Validation script not found at {GATE_SCRIPT}"
        log_failure(error_msg, logger)
        logger.error(error_msg)
        return 1

    try:
        logger.info("Invoking citation validator (T007a)...")
        # Run the validation script
        result = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Log stdout/stderr if present
        if result.stdout:
            logger.info("Validator stdout:\n" + result.stdout)
        if result.stderr:
            logger.warning("Validator stderr:\n" + result.stderr)

        if result.returncode == 0:
            logger.info("Pipeline gate PASSED. Citations validated successfully.")
            return 0
        else:
            # Determine failure reason from output or generic message
            failure_reason = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not failure_reason:
                failure_reason = f"Validator exited with code {result.returncode} without output."
            
            log_failure(failure_reason, logger)
            logger.error(f"Pipeline gate FAILED. Aborting pipeline execution.")
            return 1

    except FileNotFoundError:
        error_msg = f"Python interpreter not found or script path invalid: {GATE_SCRIPT}"
        log_failure(error_msg, logger)
        logger.error(error_msg)
        return 1
    except Exception as e:
        error_msg = f"Unexpected error during gate check: {str(e)}"
        log_failure(error_msg, logger)
        logger.exception(error_msg)
        return 1

def main():
    """Entry point for the pipeline gate."""
    exit_code = run_pipeline_gate()
    if exit_code != 0:
        # Raise SystemExit to abort the pipeline immediately as per spec
        raise SystemExit(1)
    
    # If successful, return 0 (implicit in normal exit, but explicit for clarity)
    sys.exit(0)

if __name__ == "__main__":
    main()