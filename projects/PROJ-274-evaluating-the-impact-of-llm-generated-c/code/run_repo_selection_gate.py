import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Ensure project paths are set up if not already
try:
    from utils.setup_paths import ensure_project_dirs
    ensure_project_dirs()
except ImportError:
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verify_data_freshness(file_path: Path, max_age_minutes: int = 60) -> bool:
    """
    Verify that the file was generated in the current run session.
    Checks modification time < max_age_minutes.
    """
    if not file_path.exists():
        logger.error(f"Data freshness check failed: File not found: {file_path}")
        return False

    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    now = datetime.now()
    age = now - mtime

    if age > timedelta(minutes=max_age_minutes):
        logger.error(f"Data freshness check failed: File {file_path} is stale. Age: {age}, Max allowed: {max_age_minutes} mins.")
        return False

    logger.info(f"Data freshness check passed for {file_path}. Age: {age}")
    return True

def verify_tolerances(file_path: Path) -> bool:
    """
    Verify that repo_selection_rubric.json confirms all selected repositories
    meet the ±15% tolerance criteria and high-quality rubric.
    Returns True if gate passes, False if it fails (pipeline should abort).
    """
    if not file_path.exists():
        logger.error(f"Verification failed: File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Verification failed: Invalid JSON in {file_path}: {e}")
        return False

    # Structure expected: {selected_repos: [...], tolerance_check: {loc: bool, cc: bool}}
    if 'tolerance_check' not in data:
        logger.error("Verification failed: 'tolerance_check' key missing in repo_selection_rubric.json")
        return False

    tolerance_check = data['tolerance_check']
    loc_ok = tolerance_check.get('loc', False)
    cc_ok = tolerance_check.get('cc', False)

    if not loc_ok or not cc_ok:
        logger.error("Verification failed: Tolerance check failed. LOC: {}, CC: {}".format(loc_ok, cc_ok))
        logger.error("Pipeline ABORTED due to tolerance failure.")
        return False

    # Check selected_repos is not empty
    if 'selected_repos' not in data or not data['selected_repos']:
        logger.error("Verification failed: No selected repositories found in rubric.")
        return False

    logger.info("Verification passed: All selected repositories meet tolerance criteria.")
    return True

def main():
    """
    Main entry point for T021f: Verify repo selection rubric.
    This is a GATE task. If it fails, the pipeline must abort.
    """
    project_root = Path(__file__).resolve().parents[1]
    rubric_path = project_root / "data" / "raw" / "repo_selection_rubric.json"

    logger.info(f"Starting T021f Gate: Verifying {rubric_path}")

    # 1. Check Data Freshness
    if not verify_data_freshness(rubric_path, max_age_minutes=60):
        logger.critical("Gate T021f FAILED: Data freshness check failed. Pipeline aborted.")
        sys.exit(1)

    # 2. Verify Tolerances
    if not verify_tolerances(rubric_path):
        logger.critical("Gate T021f FAILED: Tolerance verification failed. Pipeline aborted.")
        sys.exit(1)

    # 3. Success - Create a log file or lock file to indicate pass (optional but good practice)
    # We can write a small success log to data/reports/ or similar, but the task
    # primarily requires the script to run and exit 0 if passed.
    success_log = project_root / "data" / "reports" / "gate_t021f_success.json"
    success_log.parent.mkdir(parents=True, exist_ok=True)
    with open(success_log, 'w') as f:
        json.dump({
            "gate": "T021f",
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "rubric_file": str(rubric_path)
        }, f, indent=2)

    logger.info("Gate T021f PASSED. Pipeline can proceed to T021e and T076.")
    sys.exit(0)

if __name__ == "__main__":
    main()