"""
Pre-Ingestion Validation Gate (All Sources) - Task T006

Aggregates results from Phase 0 tasks (T000-run) and verifies that all
required data artifacts exist before proceeding to ingestion and modeling.

Artifacts checked:
- data/raw/moral_machine.csv.gz (from T000)
- data/raw/era5_full.parquet (from T002d/T002e)

If any validation fails, raises an exception to abort the pipeline and
updates the project state status to 'blocked'.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports if run as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Configure logger
logger = get_data_quality_logger()

def ensure_directories():
    """Ensure all required log directories exist."""
    log_dir = project_root / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def load_json_log(path: Path) -> dict:
    """Load a JSON log file if it exists, otherwise return empty dict."""
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def check_file_exists(path: Path, artifact_name: str) -> bool:
    """
    Check if a file exists and is non-empty.
    Returns True if valid, False otherwise.
    """
    if not path.exists():
        logger.error(f"MISSING: {artifact_name} not found at {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"EMPTY: {artifact_name} at {path} is empty")
        return False
    logger.info(f"FOUND: {artifact_name} at {path} ({path.stat().st_size} bytes)")
    return True

def update_project_state(status: str, reason: str):
    """
    Update the project state YAML file to reflect the validation gate status.
    """
    state_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Cannot update status.")
        return

    try:
        import yaml
        with open(state_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}

        state['validation_gate'] = {
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'reason': reason
        }

        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Updated project state to '{status}'")
    except Exception as e:
        logger.error(f"Failed to update project state: {e}")

def run_validation_gate():
    """
    Main validation logic.
    Returns True if all checks pass, False otherwise.
    """
    log_dir = ensure_directories()
    log_file = log_dir / "data_validation_log.txt"

    # Setup file handler for this specific gate log
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("=" * 60)
    logger.info("Starting Pre-Ingestion Validation Gate (T006)")
    logger.info("=" * 60)

    # Define required artifacts
    required_artifacts = {
        "moral_machine_dataset": project_root / "data" / "raw" / "moral_machine.csv.gz",
        "era5_full_dataset": project_root / "data" / "raw" / "era5_full.parquet"
    }

    all_valid = True
    missing_artifacts = []

    for name, path in required_artifacts.items():
        if not check_file_exists(path, name):
            all_valid = False
            missing_artifacts.append(name)

    # Final status
    if all_valid:
        logger.info("VALIDATION PASSED: All required data artifacts are present and non-empty.")
        update_project_state("passed", "All data artifacts verified.")
        logger.info("Proceeding to Phase 1 (Ingestion).")
    else:
        error_msg = f"VALIDATION FAILED: Missing artifacts: {', '.join(missing_artifacts)}"
        logger.error(error_msg)
        update_project_state("blocked", error_msg)
        logger.info("Pipeline ABORTED. Fix missing data sources and re-run Phase 0.")

    # Remove file handler to avoid duplicate logs
    logger.removeHandler(file_handler)

    return all_valid

def main():
    """Entry point for the validation gate."""
    try:
        success = run_validation_gate()
        if not success:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected error during validation gate: {e}")
        update_project_state("blocked", f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
