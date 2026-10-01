import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        Path("results/logs"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/external"),
        Path("state/projects"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_json_log(file_path: Path) -> dict:
    """Load a JSON log file if it exists, otherwise return an empty dict."""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not load JSON log {file_path}: {e}")
            return {}
    return {}

def check_file_exists(file_path: Path, logger: logging.Logger) -> bool:
    """Check if a file exists and is non-empty."""
    if not file_path.exists():
        logger.error(f"Required file missing: {file_path}")
        return False
    if file_path.stat().st_size == 0:
        logger.error(f"Required file is empty: {file_path}")
        return False
    return True

def check_directory_exists(dir_path: Path, logger: logging.Logger) -> bool:
    """Check if a directory exists and contains at least one file."""
    if not dir_path.exists():
        logger.error(f"Required directory missing: {dir_path}")
        return False
    if not any(dir_path.iterdir()):
        logger.error(f"Required directory is empty: {dir_path}")
        return False
    return True

def update_project_state(status: str, logger: logging.Logger):
    """Update the project state YAML file."""
    state_file = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
    ensure_directories()
    
    state_data = {
        "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Simple YAML writing without external dependency if possible, 
    # but we assume pyyaml is available based on T008
    try:
        import yaml
        with open(state_file, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Project state updated to '{status}' in {state_file}")
    except ImportError:
        # Fallback to manual string formatting if yaml is missing
        content = f"project_id: PROJ-743-ambient-temperature-influence-on-moral-d\nstatus: {status}\nupdated_at: {state_data['updated_at']}\n"
        with open(state_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.warning("PyYAML not found, writing manual YAML. Project state updated.")

def run_validation_gate(logger: logging.Logger) -> bool:
    """
    Aggregate results from T000-gate and verify that:
    1. data/raw/era5_raw_chunks/ exists and is not empty
    2. data/raw/moral_machine.csv.gz exists and is not empty
    
    Returns True if gate passes, False otherwise.
    """
    moral_machine_path = Path("data/raw/moral_machine.csv.gz")
    era5_chunks_path = Path("data/raw/era5_raw_chunks")
    validation_log_path = Path("results/logs/data_validation_log.txt")
    
    gate_passed = True

    # Check Moral Machine dataset
    if not check_file_exists(moral_machine_path, logger):
        gate_passed = False
    
    # Check ERA5 raw chunks directory
    if not check_directory_exists(era5_chunks_path, logger):
        gate_passed = False

    # Log final status
    timestamp = datetime.now().isoformat()
    with open(validation_log_path, 'a', encoding='utf-8') as f:
        if gate_passed:
            f.write(f"[{timestamp}] Pre-Ingestion Gate: PASS\n")
            logger.info("Pre-Ingestion Validation Gate: PASS")
        else:
            f.write(f"[{timestamp}] Pre-Ingestion Gate: FAIL\n")
            logger.error("Pre-Ingestion Validation Gate: FAIL")
    
    return gate_passed

def main():
    """Main entry point for T006."""
    setup_logging()
    logger = get_data_quality_logger()
    
    logger.info("Starting Pre-Ingestion Validation Gate (T006)")
    
    ensure_directories()
    
    try:
        is_valid = run_validation_gate(logger)
        
        if not is_valid:
            update_project_state("blocked", logger)
            logger.error("Validation failed. Pipeline blocked.")
            sys.exit(1)
        else:
            update_project_state("ready", logger)
            logger.info("Validation passed. Pipeline ready.")
            sys.exit(0)
            
    except Exception as e:
        logger.exception(f"Critical error during validation gate: {e}")
        update_project_state("blocked", logger)
        sys.exit(1)

if __name__ == "__main__":
    main()
