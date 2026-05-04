"""
Initialize and update project state file with artifact checksums.

Constitution Principle III: Data Integrity
- All artifacts must have SHA256 checksums recorded
- State file tracks all project artifacts for reproducibility
- Automated updates when artifacts change

Usage:
    python code/scripts/init_state_file.py [--update-all] [--verify-only]
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum_sha256(file_path: Path) -> Optional[str]:
    """Compute SHA256 checksum for a file."""
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
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

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    if not file_path.exists():
        return 0
    return file_path.stat().st_size

def get_file_modified_time(file_path: Path) -> Optional[str]:
    """Get file modification time as ISO string."""
    if not file_path.exists():
        return None
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime).isoformat()

def scan_directory_for_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Scan directory for files with given extensions."""
    if extensions is None:
        extensions = ['.py', '.yaml', '.yml', '.md', '.txt', '.json', '.csv']

    files = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return files

    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))

    return files

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or return empty structure."""
    if state_path.exists():
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    return {
        'project_id': None,
        'artifacts': {},
        'compliance': {},
        'update_history': []
    }

def save_state_file(state_path: Path, state: Dict[str, Any]) -> bool:
    """Save state file with proper formatting."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        return False

def update_artifact_checksum(artifact_entry: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
    """Update checksum, size, and modified time for an artifact entry."""
    checksum = compute_file_checksum_sha256(file_path)
    size = get_file_size(file_path)
    modified = get_file_modified_time(file_path)

    artifact_entry['checksum'] = checksum
    artifact_entry['size_bytes'] = size
    artifact_entry['last_modified'] = modified

    return artifact_entry

def update_all_checksums(state: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """Update checksums for all artifacts in state file."""
    updated = False

    # Process code artifacts
    if 'artifacts' in state and 'code' in state['artifacts']:
        for artifact in state['artifacts']['code']:
            file_path = project_root / artifact['path']
            if file_path.exists():
                old_checksum = artifact.get('checksum')
                artifact = update_artifact_checksum(artifact, file_path)
                if old_checksum != artifact.get('checksum'):
                    updated = True

    # Process data artifacts (directories)
    if 'artifacts' in state and 'data' in state['artifacts']:
        for artifact in state['artifacts']['data']:
            path = artifact['path']
            if path.endswith('/'):
                # Directory - compute combined checksum
                dir_path = project_root / path.rstrip('/')
                if dir_path.exists():
                    files = scan_directory_for_files(dir_path)
                    combined_hash = hashlib.sha256()
                    total_size = 0
                    for f in files:
                        checksum = compute_file_checksum_sha256(f)
                        if checksum:
                            combined_hash.update(checksum.encode())
                        total_size += get_file_size(f)
                    old_checksum = artifact.get('checksum')
                    artifact['checksum'] = combined_hash.hexdigest()
                    artifact['size_bytes'] = total_size
                    artifact['last_modified'] = get_file_modified_time(dir_path)
                    if old_checksum != artifact.get('checksum'):
                        updated = True
            else:
                file_path = project_root / path
                if file_path.exists():
                    old_checksum = artifact.get('checksum')
                    artifact = update_artifact_checksum(artifact, file_path)
                    if old_checksum != artifact.get('checksum'):
                        updated = True

    # Process other artifact categories (specs, config, tests)
    for category in ['specs', 'config', 'tests']:
        if 'artifacts' in state and category in state['artifacts']:
            for artifact in state['artifacts'][category]:
                path = artifact['path']
                if path.endswith('/'):
                    dir_path = project_root / path.rstrip('/')
                    if dir_path.exists():
                        files = scan_directory_for_files(dir_path)
                        combined_hash = hashlib.sha256()
                        total_size = 0
                        for f in files:
                            checksum = compute_file_checksum_sha256(f)
                            if checksum:
                                combined_hash.update(checksum.encode())
                            total_size += get_file_size(f)
                        old_checksum = artifact.get('checksum')
                        artifact['checksum'] = combined_hash.hexdigest()
                        artifact['size_bytes'] = total_size
                        artifact['last_modified'] = get_file_modified_time(dir_path)
                        if old_checksum != artifact.get('checksum'):
                            updated = True
                else:
                    file_path = project_root / path
                    if file_path.exists():
                        old_checksum = artifact.get('checksum')
                        artifact = update_artifact_checksum(artifact, file_path)
                        if old_checksum != artifact.get('checksum'):
                            updated = True

    return state, updated

def verify_state_checksums(state: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """Verify all checksums match current file states."""
    verification_results = {
        'verified': True,
        'mismatches': [],
        'missing_files': [],
        'total_artifacts': 0,
        'verified_count': 0
    }

    all_categories = ['code', 'data', 'specs', 'config', 'tests']

    for category in all_categories:
        if 'artifacts' not in state or category not in state['artifacts']:
            continue

        for artifact in state['artifacts'][category]:
            path = artifact['path']
            verification_results['total_artifacts'] += 1

            # Skip directory entries for individual file verification
            if path.endswith('/'):
                continue

            file_path = project_root / path

            if not file_path.exists():
                verification_results['missing_files'].append(path)
                verification_results['verified'] = False
                continue

            current_checksum = compute_file_checksum_sha256(file_path)
            stored_checksum = artifact.get('checksum')

            if stored_checksum is None:
                verification_results['mismatches'].append({
                    'path': path,
                    'reason': 'No stored checksum'
                })
                verification_results['verified'] = False
            elif current_checksum != stored_checksum:
                verification_results['mismatches'].append({
                    'path': path,
                    'stored': stored_checksum,
                    'current': current_checksum
                })
                verification_results['verified'] = False
            else:
                verification_results['verified_count'] += 1

    return verification_results

def main():
    """Main entry point for state file initialization and updates."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Initialize and update project state file with artifact checksums'
    )
    parser.add_argument(
        '--update-all',
        action='store_true',
        help='Update all checksums in state file'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify checksums without updating'
    )
    parser.add_argument(
        '--state-file',
        type=str,
        default='state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml',
        help='Path to state file'
    )
    args = parser.parse_args()

    # Determine project root (assume script is in code/scripts/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    state_path = project_root / args.state_file

    logger.info(f"Project root: {project_root}")
    logger.info(f"State file: {state_path}")

    if args.verify_only:
        # Verify mode
        if not state_path.exists():
            logger.error(f"State file does not exist: {state_path}")
            sys.exit(1)

        state = load_state_file(state_path)
        results = verify_state_checksums(state, project_root)

        logger.info(f"Verification complete:")
        logger.info(f"  Total artifacts: {results['total_artifacts']}")
        logger.info(f"  Verified: {results['verified_count']}")
        logger.info(f"  Missing: {len(results['missing_files'])}")
        logger.info(f"  Mismatches: {len(results['mismatches'])}")

        if results['mismatches']:
            logger.warning("Checksum mismatches found:")
            for m in results['mismatches'][:10]:  # Show first 10
                logger.warning(f"  {m['path']}: {m.get('reason', 'mismatch')}")

        if results['verified']:
            logger.info("All checksums verified successfully")
            sys.exit(0)
        else:
            logger.error("Checksum verification failed")
            sys.exit(1)

    else:
        # Update mode (default)
        logger.info("Initializing/updating state file...")

        # Load existing state or create new
        state = load_state_file(state_path)

        # Update project metadata
        state['project_id'] = 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete'
        state['last_updated'] = datetime.now().isoformat()

        # Update all checksums
        state, updated = update_all_checksums(state, project_root)

        # Add update history entry
        state['update_history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'checksum_update',
            'script': 'code/scripts/init_state_file.py',
            'changes': f'Updated {sum(1 for cat in ["code","data","specs","config","tests"] if cat in state.get("artifacts", {}))} artifact categories'
        })

        # Save state file
        if save_state_file(state_path, state):
            logger.info(f"State file updated successfully: {state_path}")
            logger.info(f"Checksums updated: {updated}")

            # Run verification after update
            results = verify_state_checksums(state, project_root)
            logger.info(f"Post-update verification: {results['verified_count']}/{results['total_artifacts']} artifacts verified")
        else:
            logger.error("Failed to save state file")
            sys.exit(1)

    logger.info("State file operation complete")

if __name__ == '__main__':
    main()
