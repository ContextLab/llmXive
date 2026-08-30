import hashlib
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_artifact_files(directory: str = 'artifacts') -> List[str]:
    """Get all artifact files in directory."""
    path = Path(directory)
    if not path.exists():
        return []
    return [str(f) for f in path.rglob('*') if f.is_file()]

def generate_artifact_hashes(files: List[str]) -> Dict[str, str]:
    """Generate hashes for artifact files."""
    return {f: calculate_sha256(f) for f in files}

def load_state(state_path: str = 'artifacts/state.yaml') -> Dict:
    """Load previous state."""
    path = Path(state_path)
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_state(state: Dict, state_path: str = 'artifacts/state.yaml') -> None:
    """Save state to YAML."""
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(state, f)

def update_state_with_hashes(state: Dict, new_hashes: Dict[str, str]) -> Dict:
    """Update state with new hashes."""
    state['hashes'] = new_hashes
    state['updated_at'] = datetime.now().isoformat()
    return state

def main():
    """Generate and store artifact hashes."""
    files = get_artifact_files()
    if not files:
        print("No artifact files found.")
        return 0
    
    hashes = generate_artifact_hashes(files)
    state = load_state()
    state = update_state_with_hashes(state, hashes)
    save_state(state)
    
    print(f"Generated hashes for {len(files)} artifacts")
    return 0

if __name__ == '__main__':
    sys.exit(main())
