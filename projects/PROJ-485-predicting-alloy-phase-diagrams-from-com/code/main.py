"""
Main pipeline orchestrator for predicting alloy phase diagrams.
Executes the minimal pipeline needed for T001: provenance generation.
"""
import os
import sys
import argparse
import json
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_file_sha256
from utils.config import get_config, validate_data_sources
from utils.error_codes import ErrorCode
from setup_data_directories import create_directories as setup_dirs
from features.seed_elemental_properties import main as seed_properties
from provenance import generate_provenance

logger = get_logger(__name__)

def ensure_state_directory():
    """Ensure the state directory exists."""
    state_dir = "state/PROJ-485"
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def load_state(state_file):
    """Load state from YAML/JSON file."""
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"steps": {}, "artifacts": {}}

def save_state(state_file, state):
    """Save state to YAML/JSON file."""
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

def update_step_status(state_file, step_name, status, details=None):
    """Update the status of a pipeline step."""
    state = load_state(state_file)
    state["steps"][step_name] = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    save_state(state_file, state)

def update_artifact_hash(state_file, artifact_name, file_path):
    """Compute and store SHA-256 hash of an artifact."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    hash_value = compute_file_sha256(file_path)
    state = load_state(state_file)
    state["artifacts"][artifact_name] = {
        "path": file_path,
        "sha256": hash_value,
        "timestamp": datetime.now().isoformat()
    }
    save_state(state_file, state)

def run_step(step_name, func, state_file, *args, **kwargs):
    """Run a pipeline step with logging and state update."""
    log_info(logger, f"Starting step: {step_name}")
    update_step_status(state_file, step_name, "running")
    try:
        func(*args, **kwargs)
        update_step_status(state_file, step_name, "completed")
        log_info(logger, f"Completed step: {step_name}")
        return True
    except Exception as e:
        log_error(logger, f"Step {step_name} failed: {str(e)}")
        update_step_status(state_file, step_name, "failed", {"error": str(e)})
        return False

def run_provenance(state_file):
    """Generate provenance information for raw inputs."""
    generate_provenance()
    update_artifact_hash(state_file, "provenance", "data/provenance.json")
    update_artifact_hash(state_file, "raw_checksum", "data/raw/checksum.sha256")

def run_pipeline(args):
    """Run the minimal pipeline required for T001."""
    state_file = "state/PROJ-485/pipeline_state.json"
    ensure_state_directory()
    save_state(state_file, {"steps": {}, "artifacts": {}})

    # Step 0: Setup directories
    log_info(logger, "Setting up data directories...")
    setup_dirs()

    # Step 1: Seed elemental properties if missing (required for later steps)
    if not os.path.exists("data/raw/elemental_properties.csv"):
        seed_properties()
        update_artifact_hash(state_file, "elemental_properties", "data/raw/elemental_properties.csv")

    # Step 2: Provenance generation (core of T001)
    if not run_step("provenance", run_provenance, state_file):
        return False

    # All required artifacts for T001 have been produced; exit successfully.
    log_info(logger, "T001 completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Alloy Phase Diagram Prediction Pipeline (T001)")
    parser.add_argument("--compliance", action="store_true", help="Run compliance check at end")
    args = parser.parse_args()

    try:
        success = run_pipeline(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        log_error(logger, f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()