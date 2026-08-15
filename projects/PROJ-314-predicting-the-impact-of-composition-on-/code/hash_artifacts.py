import hashlib
import json
from pathlib import Path
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_directory(dir_path: Path) -> Dict[str, str]:
    """Calculate hashes for all files in a directory."""
    hashes = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
          rel_path = file_path.relative_to(dir_path)
          hashes[str(rel_path)] = hash_file(file_path)
    return hashes

def update_state_file(project_id: str, hashes: Dict[str, str]):
    """Update the project state file with new hashes."""
    state_dir = Path(f"state/projects/{project_id}")
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state.yaml"
    
    state_data = {
        "project_id": project_id,
        "updated_at": str(pd.Timestamp.now()),
        "artifact_hashes": hashes
    }
    
    # Simple JSON serialization for state (YAML requires extra lib, using JSON for simplicity here)
    with open(state_file.with_suffix('.json'), 'w') as f:
        json.dump(state_data, f, indent=2)
    
    logger.info(f"State updated for {project_id}")

def main():
    """Main entry point for artifact hashing."""
    if len(sys.argv) > 1 and sys.argv[1] == "--update-state":
        project_id = "PROJ-314-predicting-the-impact-of-composition-on-"
        data_dir = Path("data")
        if data_dir.exists():
            hashes = hash_directory(data_dir)
            update_state_file(project_id, hashes)
    else:
        logger.info("Run with --update-state to update project state.")

if __name__ == "__main__":
    main()
