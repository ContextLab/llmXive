"""
Update state file checksums when artifacts change.

Constitution Principle III: Data Integrity
- Automated state file updates
- Used in CI/CD when artifacts are modified
- Can be called programmatically or via CLI

Usage:
    python code/scripts/update_state_checksums.py
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum_sha256(file_path: Path) -> Optional[str]:
    """Compute SHA256 checksum for a file."""
    if not file_path.exists():
        return None

    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load state file."""
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")

    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state_file(state_path: Path, state: Dict[str, Any]) -> bool:
    """Save state file."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        return False

def update_artifact_checksums(state: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """Update checksums for all artifacts."""
    all_categories = ['code', 'data', 'specs', 'config', 'tests']

    for category in all_categories:
        if 'artifacts' not in state or category not in state['artifacts']:
            continue

        for artifact in state['artifacts'][category]:
            path = artifact['path']

            if path.endswith('/'):
                # Directory - compute combined checksum
                dir_path = project_root / path.rstrip('/')
                if dir_path.exists():
                    files = [f for f in dir_path.rglob('*') if f.is_file()]
                    combined_hash = hashlib.sha256()
                    total_size = 0

                    for f in sorted(files):
                        checksum = compute_file_checksum_sha256(f)
                        if checksum:
                            combined_hash.update(checksum.encode())
                        total_size += f.stat().st_size

                    artifact['checksum'] = combined_hash.hexdigest()
                    artifact['size_bytes'] = total_size
                    artifact['last_modified'] = datetime.fromtimestamp(
                        max(f.stat().st_mtime for f in files) if files else 0
                    ).isoformat()
            else:
                # File
                file_path = project_root / path
                if file_path.exists():
                    artifact['checksum'] = compute_file_checksum_sha256(file_path)
                    artifact['size_bytes'] = file_path.stat().st_size
                    artifact['last_modified'] = datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()

    return state

def main():
    """Main entry point."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    state_path = project_root / 'state' / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml'

    logger.info(f"Updating state file: {state_path}")

    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        logger.error("Run code/scripts/init_state_file.py first")
        sys.exit(1)

    try:
        state = load_state_file(state_path)
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        sys.exit(1)

    state = update_artifact_checksums(state, project_root)
    state['last_updated'] = datetime.now().isoformat()

    if save_state_file(state_path, state):
        logger.info(f"State file updated: {state_path}")
    else:
        logger.error("Failed to update state file")
        sys.exit(1)

if __name__ == '__main__':
    main()
