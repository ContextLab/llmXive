import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(directory_path: str) -> str:
    """Compute a combined SHA-256 hash for all files in a directory tree."""
    sha256_hash = hashlib.sha256()
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Sort files to ensure deterministic ordering
    files = sorted(dir_path.rglob("*"))
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash calculation for uniqueness
            relative_path = str(file_path.relative_to(dir_path))
            sha256_hash.update(relative_path.encode('utf-8'))
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_sha256_string(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def collect_all_artifact_hashes(data_dir: str) -> Dict[str, str]:
    """Collect SHA-256 hashes for all files in the data directory tree."""
    artifacts = {}
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    for file_path in sorted(data_path.rglob("*")):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(data_path))
            artifacts[relative_path] = compute_sha256(str(file_path))
    return artifacts

def update_state_registry(
    state_file_path: str,
    reproducibility_hash: str,
    final_verification_timestamp: str,
    additional_artifacts: Optional[Dict[str, str]] = None
) -> None:
    """
    Update the project state registry with the final reproducibility hash
    and verification timestamp.
    
    Args:
        state_file_path: Path to the state YAML file
        reproducibility_hash: SHA-256 hash of the entire data directory
        final_verification_timestamp: ISO8601 timestamp string
        additional_artifacts: Optional dict of additional artifact hashes to include
    """
    state_path = Path(state_file_path)
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_file_path}")
    
    # Load existing state
    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f)
    
    # Update with new fields
    state_data["reproducibility_hash"] = reproducibility_hash
    state_data["final_verification_timestamp"] = final_verification_timestamp
    
    if additional_artifacts:
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}
        state_data["artifact_hashes"].update(additional_artifacts)
    
    # Write back
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for finalizing the state registry."""
    project_root = Path(__file__).parent.parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-866-llmxive-follow-up-extending-foundation-p.yaml"
    data_dir = project_root / "data"
    
    if not state_file.exists():
        print(f"Error: State file not found: {state_file}")
        sys.exit(1)
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    try:
        # Compute reproducibility hash
        print(f"Computing reproducibility hash for {data_dir}...")
        reproducibility_hash = compute_directory_hash(str(data_dir))
        
        # Generate timestamp
        final_verification_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Update state registry
        print(f"Updating state registry at {state_file}...")
        update_state_registry(
            str(state_file),
            reproducibility_hash,
            final_verification_timestamp
        )
        
        print(f"State registry updated successfully.")
        print(f"Reproducibility Hash: {reproducibility_hash}")
        print(f"Final Verification Timestamp: {final_verification_timestamp}")
        
    except Exception as e:
        print(f"Error updating state registry: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
