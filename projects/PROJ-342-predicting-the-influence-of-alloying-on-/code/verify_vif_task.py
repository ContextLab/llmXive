"""
T035b Verification Script.
This script programmatically verifies the output of T035a.
It asserts that data/processed/vif_diagnostic_log.json exists and contains
the 'flagged_features' key.
"""
import sys
import json
import logging
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analyze import get_project_root

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_vif_task():
    """
    Verifies T035b requirements:
    1. File data/processed/vif_diagnostic_log.json exists.
    2. File contains 'flagged_features' key.
    """
    project_root = get_project_root()
    log_path = project_root / "data" / "processed" / "vif_diagnostic_log.json"

    logger.info(f"Checking for VIF diagnostic log at: {log_path}")

    # Check 1: File existence
    if not log_path.exists():
        logger.error("VERIFICATION FAILED: File does not exist.")
        logger.error("Hint: Run 'python code/analyze.py --task vif' or ensure T035a has completed.")
        return False

    # Check 2: Valid JSON and key presence
    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"VERIFICATION FAILED: Invalid JSON in {log_path}. Error: {e}")
        return False

    if "flagged_features" not in data:
        logger.error("VERIFICATION FAILED: 'flagged_features' key missing in JSON.")
        logger.error(f"Found keys: {list(data.keys())}")
        return False

    flagged = data["flagged_features"]
    if not isinstance(flagged, list):
        logger.error(f"VERIFICATION FAILED: 'flagged_features' is not a list. Type: {type(flagged)}")
        return False

    logger.info("VERIFICATION PASSED:")
    logger.info(f"  - File exists: {log_path}")
    logger.info(f"  - 'flagged_features' key present: True")
    logger.info(f"  - Flagged features count: {len(flagged)}")
    if flagged:
        logger.info(f"  - Flagged features: {flagged}")
    else:
        logger.info("  - No features flagged (VIF <= 5 for all).")

    return True

if __name__ == "__main__":
    success = verify_vif_task()
    sys.exit(0 if success else 1)