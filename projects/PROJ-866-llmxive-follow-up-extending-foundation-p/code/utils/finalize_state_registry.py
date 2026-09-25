import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> str:
    """
    Compute a deterministic SHA-256 hash of an entire directory tree.
    Files are sorted by relative path to ensure determinism.
    """
    if not dir_path.exists():
        return ""
    
    hasher = hashlib.sha256()
    # Collect all files, sorted by relative path for determinism
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            if filename.endswith('.pyc') or filename == '.gitkeep':
                continue
            full_path = Path(root) / filename
            rel_path = full_path.relative_to(dir_path)
            files.append((str(rel_path), full_path))
    
    files.sort(key=lambda x: x[0])
    
    for rel_path, full_path in files:
        # Hash the relative path first
        hasher.update(rel_path.encode('utf-8'))
        # Then hash the file content
        hasher.update(compute_sha256(full_path).encode('utf-8'))
    
    return hasher.hexdigest()

def collect_all_artifact_hashes(data_dir: Path) -> Dict[str, str]:
    """Collect hashes for all relevant data directories."""
    hashes = {}
    
    if (data_dir / "raw").exists():
        hashes["raw"] = compute_directory_hash(data_dir / "raw")
    
    if (data_dir / "processed").exists():
        hashes["processed"] = compute_directory_hash(data_dir / "processed")
    
    if (data_dir / "results").exists():
        hashes["results"] = compute_directory_hash(data_dir / "results")
    
    return hashes

def update_state_registry(
    state_path: Path, 
    data_dir: Path,
    reproducibility_hash: str
) -> None:
    """
    Update the project state registry with final verification data.
    
    Args:
        state_path: Path to the state YAML file
        data_dir: Path to the data directory (to compute directory hash)
        reproducibility_hash: The pre-computed hash of the entire data tree
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f)
    
    # Update with final verification data
    state_data['final_verification'] = {
        'reproducibility_hash': reproducibility_hash,
        'final_verification_timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_artifact_hashes': collect_all_artifact_hashes(data_dir)
    }
    
    # Ensure project metadata is up to date
    state_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def main():
    """CLI entry point for finalizing state registry."""
    project_root = Path(__file__).parent.parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-866-llmxive-follow-up-extending-foundation-p.yaml"
    data_dir = project_root / "data"
    
    if not state_file.exists():
        print(f"Error: State file not found at {state_file}")
        sys.exit(1)
    
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        sys.exit(1)
    
    # Compute the full directory hash
    reproducibility_hash = compute_directory_hash(data_dir)
    print(f"Computed reproducibility hash: {reproducibility_hash}")
    
    # Update the state registry
    update_state_registry(state_file, data_dir, reproducibility_hash)
    print(f"Successfully updated state registry at {state_file}")

if __name__ == "__main__":
    main()
