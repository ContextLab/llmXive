"""
Verification script for T032.
Checks that the project state file has been updated to 'implemented'.
"""
import os
import sys
import logging
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ID = "PROJ-150-detecting-statistical-power-drift-in-rep"
STATE_DIR = Path("state") / "projects" / PROJECT_ID
STATE_FILE = STATE_DIR / "state.yaml"
TARGET_STAGE = "implemented"

def verify_state_file():
    """
    Verifies that state.yaml exists and contains current_stage: implemented.
    Returns True if valid, False otherwise.
    """
    if not STATE_FILE.exists():
        logger.error(f"State file not found at: {STATE_FILE}")
        return False

    try:
        with open(STATE_FILE, 'r') as f:
            state_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML in {STATE_FILE}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading {STATE_FILE}: {e}")
        return False

    if not isinstance(state_data, dict):
        logger.error(f"State file content is not a dictionary: {state_data}")
        return False

    current_stage = state_data.get('current_stage')
    
    if current_stage != TARGET_STAGE:
        logger.error(
            f"State check failed. Expected current_stage='{TARGET_STAGE}', "
            f"but found current_stage='{current_stage}'."
        )
        return False

    logger.info(f"Success: {STATE_FILE} contains current_stage: {TARGET_STAGE}")
    return True

def main():
    """Entry point for verification."""
    logger.info(f"Verifying state for project: {PROJECT_ID}")
    if not STATE_DIR.exists():
        logger.error(f"State directory does not exist: {STATE_DIR}")
        sys.exit(1)

    success = verify_state_file()
    
    if success:
        logger.info("Task T032 verification PASSED.")
        sys.exit(0)
    else:
        logger.error("Task T032 verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
