"""
Artifact hashing and state management.
Implements T005, T044.
"""
import hashlib
import json
from pathlib import Path
import logging
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/hashing.log')
    ]
)
logger = logging.getLogger(__name__)

def hash_file(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_directory(dirpath: str) -> Dict[str, str]:
    """Compute hashes for all files in a directory."""
    hashes = {}
    dir_path = Path(dirpath)
    if not dir_path.exists():
        return hashes
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
          hashes[str(file_path)] = hash_file(str(file_path))
    return hashes

def update_state_file(project_id: str = 'PROJ-314-predicting-the-impact-of-composition-on-'):
    """Update project state with new content hashes."""
    state_dir = Path('state/projects')
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f'{project_id}.yaml'
    
    # Compute hashes
    data_hashes = hash_directory('data')
    code_hashes = hash_directory('code')
    
    state = {
        'project_id': project_id,
        'updated_at': '2024-01-01T00:00:00Z',
        'artifact_hashes': {
            'data': data_hashes,
            'code': code_hashes
        }
    }
    
    # Save as YAML (simplified JSON for now)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Updated state file: {state_file}")

def main():
    """Main hashing entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Hash artifacts and update state")
    parser.add_argument('--update-state', action='store_true', help='Update project state')
    args = parser.parse_args()
    
    try:
        if args.update_state:
            update_state_file()
            return 0
        else:
            # Default: just hash data directory
            hashes = hash_directory('data')
            print(json.dumps(hashes, indent=2))
            return 0
    except Exception as e:
        logger.error(f"Hashing failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())