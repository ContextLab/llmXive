import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from config import get_config, get_state_path
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_config, get_state_path

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_artifacts_to_hash(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Return a list of file paths that should be hashed.
    Based on the project structure, this includes generated data and results.
    """
    if config is None:
        config = get_config()
    
    artifacts = []
    
    # Raw data
    raw_csv = config.get("output_csv", "data/raw/twin_primes.csv")
    if os.path.exists(raw_csv):
        artifacts.append(raw_csv)
    
    # Results
    results_dir = config.get("results_dir", "data/results")
    if os.path.exists(results_dir):
        for root, _, files in os.walk(results_dir):
            for file in files:
                if file.endswith(".json") or file.endswith(".csv"):
                    artifacts.append(os.path.join(root, file))
    
    # Figures
    figures_dir = config.get("figures_dir", "data/figures")
    if os.path.exists(figures_dir):
        for root, _, files in os.walk(figures_dir):
            for file in files:
                if file.endswith(".png") or file.endswith(".pdf"):
                    artifacts.append(os.path.join(root, file))
    
    return artifacts

def update_state_file(state_path: str, hashes: Dict[str, str], metadata: Dict[str, Any]) -> None:
    """
    Update the project state YAML file with new hashes and metadata.
    Creates the file if it doesn't exist.
    """
    state = {"artifacts": {}}
    
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state = yaml.safe_load(f) or {"artifacts": {}}
        except yaml.YAMLError:
            state = {"artifacts": {}}
    
    # Update artifacts with hashes
    for path, hash_val in hashes.items():
        state["artifacts"][path] = {"hash": hash_val}
    
    # Merge metadata
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"].update(metadata)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Entry point to hash all artifacts and update state.
    """
    config = get_config()
    state_path = get_state_path()
    
    print(f"Computing hashes for artifacts...")
    artifacts = get_artifacts_to_hash(config)
    
    if not artifacts:
        print("No artifacts found to hash.")
        return

    hashes = {}
    for path in artifacts:
        if os.path.exists(path):
            h = compute_sha256(path)
            hashes[path] = h
            print(f"  {path}: {h[:16]}...")
        else:
            print(f"  Warning: {path} not found.")
    
    # Update state
    update_state_file(state_path, hashes, {"last_hashed": "run"})
    print(f"State updated at {state_path}")

if __name__ == "__main__":
    main()