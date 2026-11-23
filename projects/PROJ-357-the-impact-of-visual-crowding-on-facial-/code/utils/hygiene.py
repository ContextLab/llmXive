"""
Hygiene utilities for project data integrity.
Computes SHA256 checksums for data and artifacts directories and updates
the project state YAML file.

Includes execution gate validation to ensure required data files exist
before allowing the pipeline to proceed to the GLMM stage.
"""
import hashlib
import os
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Project root relative to this file (assuming code/utils/ structure)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_ID = "PROJ-357-the-impact-of-visual-crowding-on-facial-"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

# Execution Gate Validation: Required files for GLMM stage
REQUIRED_GLMM_INPUTS = [
    DATA_DIR / "processed" / "clutter_metrics.csv",
    DATA_DIR / "processed" / "human_judgments_aggregates.csv"
]


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory(directory: Path) -> dict:
    """
    Recursively scan a directory and compute SHA256 for all files.
    Returns a dict mapping relative paths to hashes.
    """
    if not directory.exists():
        return {}
    
    file_hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            file_hashes[str(relative_path)] = compute_sha256(file_path)
    
    return file_hashes


def validate_execution_gate() -> bool:
    """
    Validate that all required input files for the GLMM stage exist.
    
    Returns:
        bool: True if all required files are present, False otherwise.
        
    Raises:
        FileNotFoundError: If any required file is missing (fail loudly).
    """
    missing_files = []
    for file_path in REQUIRED_GLMM_INPUTS:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        error_msg = (
            "EXECUTION GATE FAILED: Required input files for GLMM stage are missing.\n"
            "The pipeline cannot proceed to the analysis stage without these files.\n"
            "Missing files:\n" + "\n".join(f"  - {f}" for f in missing_files) + "\n"
            "Please ensure T022 (clutter_metrics.csv) and T048 (human_judgments_aggregates.csv) have completed successfully."
        )
        # Log to stderr for immediate visibility
        print(error_msg, file=sys.stderr)
        raise FileNotFoundError(error_msg)
    
    print("Execution Gate Validation: PASSED")
    print("All required input files for GLMM stage are present.")
    return True


def update_state_file(data_hashes: dict, artifacts_hashes: dict):
    """Update the project state YAML file with new checksums."""
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    state = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f) or {}
    
    state["last_updated"] = datetime.utcnow().isoformat()
    state["checksums"] = {
        "data": data_hashes,
        "artifacts": artifacts_hashes
    }
    
    # Add execution gate status
    try:
        validate_execution_gate()
        state["execution_gate"] = {
            "status": "passed",
            "timestamp": datetime.utcnow().isoformat(),
            "required_files": [str(f) for f in REQUIRED_GLMM_INPUTS]
        }
    except FileNotFoundError as e:
        state["execution_gate"] = {
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
    
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def main():
    """Main entry point to compute checksums and update state."""
    print(f"Scanning data directory: {DATA_DIR}")
    data_hashes = scan_directory(DATA_DIR)
    
    print(f"Scanning artifacts directory: {ARTIFACTS_DIR}")
    artifacts_hashes = scan_directory(ARTIFACTS_DIR)
    
    print(f"Updating state file: {STATE_FILE}")
    update_state_file(data_hashes, artifacts_hashes)
    
    print(f"Completed. Found {len(data_hashes)} data files and {len(artifacts_hashes)} artifact files.")
    
    # Check execution gate status
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
        gate_status = state.get("execution_gate", {}).get("status", "unknown")
        if gate_status == "passed":
            print("Pipeline can proceed to GLMM stage.")
            return 0
        else:
            print("Pipeline blocked: Execution gate validation failed.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())