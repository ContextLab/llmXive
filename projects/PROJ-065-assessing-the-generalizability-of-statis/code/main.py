import os
import sys
import time
import json
import hashlib
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import from config to ensure directories exist
try:
    from config import ensure_config_dirs
except ImportError:
    # Fallback if config is not in path (should be handled by run_pipeline context)
    ensure_config_dirs = None

# Constants
PROJECT_ID = "PROJ-065-assessing-the-generalizability-of-statis"
STATE_DIR = "state/projects"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
HASH_ALGORITHM = "sha256"

def log_header(message: str):
    """Print a formatted header to stdout."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80 + "\n")

def log_step(message: str):
    """Print a formatted step to stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def calculate_file_hash(file_path: str) -> Optional[str]:
    """
    Calculate SHA-256 hash of a file.
    Returns None if file does not exist.
    """
    if not os.path.exists(file_path):
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_step(f"Error calculating hash for {file_path}: {e}")
        return None

def record_artifact_hash(artifact_path: str, state_file_path: str) -> Dict[str, Any]:
    """
    Calculate the hash of an artifact and update the project state YAML file.
    
    Args:
        artifact_path: Path to the file to hash (relative or absolute)
        state_file_path: Path to the state YAML file to update
        
    Returns:
        Dictionary containing the record update details
    """
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    file_hash = calculate_file_hash(artifact_path)
    if file_hash is None:
        raise RuntimeError(f"Failed to calculate hash for {artifact_path}")

    # Ensure state directory exists
    state_dir = os.path.dirname(state_file_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir, exist_ok=True)

    # Load existing state or initialize
    state_data = {}
    if os.path.exists(state_file_path):
        try:
            import yaml
            with open(state_file_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except ImportError:
            # Fallback if PyYAML is not installed: store as JSON-like text or simple dict
            # For robustness in this specific task, we attempt to parse a simple YAML structure manually
            # or just overwrite if parsing fails, but ideally we assume PyYAML is available via requirements.txt
            # If not, we try to read it as JSON if it was saved as JSON, else empty
            try:
                with open(state_file_path, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('{') or content.startswith('['):
                        state_data = json.loads(content)
                    else:
                        # Basic YAML-like parsing for flat keys or just reset
                        # Given the constraint of "real code", we assume standard libs or installed deps.
                        # If PyYAML is missing, we cannot safely parse complex YAML.
                        # We will attempt to use the `yaml` import which should be in requirements.txt.
                        # If it fails, we raise an error to force dependency installation.
                        raise ImportError("PyYAML is required for state management")
            except json.JSONDecodeError:
                state_data = {}
        except Exception:
            state_data = {}

    # Initialize nested structure if missing
    if 'artifacts' not in state_data:
        state_data['artifacts'] = {}
    
    if PROJECT_ID not in state_data['artifacts']:
        state_data['artifacts'][PROJECT_ID] = {}

    # Update hash and timestamp
    artifact_name = os.path.basename(artifact_path)
    state_data['artifacts'][PROJECT_ID][artifact_name] = {
        "hash": file_hash,
        "path": artifact_path,
        "updated_at": datetime.now().isoformat()
    }

    # Write back to file
    try:
        import yaml
        with open(state_file_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON if YAML is not available (though YAML is preferred for state)
        with open(state_file_path, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    log_step(f"Recorded hash for {artifact_name}: {file_hash[:16]}...")
    
    return {
        "artifact": artifact_name,
        "path": artifact_path,
        "hash": file_hash,
        "state_file": state_file_path
    }

def update_state_file(artifact_path: str):
    """
    Convenience wrapper to update the state file for a specific project.
    """
    state_file_path = os.path.join(STATE_DIR, STATE_FILE_NAME)
    return record_artifact_hash(artifact_path, state_file_path)

def run_pipeline():
    """
    Main orchestration entry point for the research pipeline.
    """
    try:
        log_header("Starting Research Pipeline for " + PROJECT_ID)
        
        # Ensure configuration directories exist
        if ensure_config_dirs:
            ensure_config_dirs()
        
        # Ensure state directory exists for this project
        state_file_path = os.path.join(STATE_DIR, STATE_FILE_NAME)
        state_dir = os.path.dirname(state_file_path)
        if not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
        
        # Example workflow: In a real run, this would call ingestion, bootstrap, etc.
        # For T010, we demonstrate the record_artifact_hash functionality.
        # We assume a hypothetical artifact was created (or we create a dummy one for demo purposes 
        # if no real data exists yet, but the function itself works on real files).
        
        # Check for processed data as a trigger to record its hash
        processed_data_path = "data/processed/baseline_metrics.csv"
        if os.path.exists(processed_data_path):
            log_step(f"Found processed data: {processed_data_path}")
            result = update_state_file(processed_data_path)
            log_step(f"State updated successfully: {result['state_file']}")
        else:
            log_step(f"Processed data not found at {processed_data_path}. Skipping hash recording for this run.")
            log_step("Note: Run ingestion first to generate data/processed/baseline_metrics.csv")

        log_header("Pipeline Execution Complete")
        return 0

    except Exception as e:
        log_step(f"Pipeline failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_pipeline())