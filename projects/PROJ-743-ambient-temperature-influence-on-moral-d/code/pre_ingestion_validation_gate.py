import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import existing utilities from the project
from config import get_path_env_override

def ensure_directories() -> None:
    """Ensure all required output directories exist."""
    dirs = [
        "results/logs",
        "state/projects",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_json_log(path: Path) -> Dict[str, Any]:
    """Load a JSON log file if it exists, otherwise return an empty dict."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def check_file_exists(path: Path) -> bool:
    """Check if a specific file exists."""
    return path.is_file()

def check_directory_exists(path: Path) -> bool:
    """Check if a specific directory exists and is not empty."""
    if not path.is_dir():
        return False
    try:
        return any(path.iterdir())
    except PermissionError:
        return False

def update_project_state(status: str, reason: str = "") -> None:
    """Update the project state YAML file."""
    state_path = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
    ensure_directories()
    
    state_data = {
        "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "last_validation": {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "reason": reason
        }
    }
    
    # Simple YAML serialization without external dependency for this specific task
    # to avoid circular dependencies if yaml is not installed in this specific context
    # though requirements.txt includes it. We write a basic YAML structure.
    with open(state_path, "w", encoding="utf-8") as f:
        f.write(f"project_id: {state_data['project_id']}\n")
        f.write(f"status: '{state_data['status']}'\n")
        f.write(f"updated_at: '{state_data['updated_at']}'\n")
        f.write("last_validation:\n")
        f.write(f"  timestamp: '{state_data['last_validation']['timestamp']}'\n")
        f.write(f"  status: '{state_data['last_validation']['status']}'\n")
        f.write(f"  reason: '{state_data['last_validation']['reason']}'\n")

def run_validation_gate() -> bool:
    """
    Run the pre-ingestion validation gate.
    
    Checks:
    1. T000-gate results (Moral Machine, ERA5 Sample, Full ERA5 validation)
    2. Existence of data/raw/era5_raw_chunks/
    3. Existence of data/raw/moral_machine.csv.gz
    
    Returns:
        bool: True if gate passes, False otherwise.
    """
    ensure_directories()
    logger = logging.getLogger("validation_gate")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    log_path = Path("results/logs/data_validation_log.txt")
    
    # 1. Check T000-gate results in the validation log
    # We look for specific "PASS" strings logged by previous tasks
    gate_checks = [
        "Moral Machine Validation: PASS",
        "ERA5 Validation: PASS",
        "Full ERA5 Validation: PASS"
    ]
    
    gate_passed = True
    missing_logs = []
    
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        
        for check in gate_checks:
            if check not in log_content:
                gate_passed = False
                missing_logs.append(check)
    else:
        gate_passed = False
        missing_logs.append(f"Validation log file {log_path} not found")

    # 2. Check data/raw/moral_machine.csv.gz
    moral_machine_path = Path("data/raw/moral_machine.csv.gz")
    if not check_file_exists(moral_machine_path):
        gate_passed = False
        missing_logs.append("data/raw/moral_machine.csv.gz missing")

    # 3. Check data/raw/era5_raw_chunks/
    era5_chunks_path = Path("data/raw/era5_raw_chunks")
    if not check_directory_exists(era5_chunks_path):
        gate_passed = False
        missing_logs.append("data/raw/era5_raw_chunks/ missing or empty")

    # Log final status
    if gate_passed:
        logger.info("Gate Open: All pre-ingestion validations passed.")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} - Pre-Ingestion Validation Gate: PASS\n")
        update_project_state("ready", "Pre-ingestion validation passed.")
        return True
    else:
        logger.error("Gate Blocked: Validation failed.")
        logger.error(f"Missing checks: {missing_logs}")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} - Pre-Ingestion Validation Gate: FAIL\n")
            f.write(f"Reason: {', '.join(missing_logs)}\n")
        update_project_state("blocked", f"Pre-ingestion validation failed: {', '.join(missing_logs)}")
        raise RuntimeError(f"Pre-ingestion validation gate failed. Missing: {', '.join(missing_logs)}")

def main() -> None:
    """Main entry point for the script."""
    try:
        run_validation_gate()
    except RuntimeError as e:
        print(f"Validation Gate Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
