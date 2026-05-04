"""
Verify state file checksums for all data files per Constitution Principle III.

This script validates that state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
contains complete and accurate checksum entries for all data files in data/raw/.

Exit codes:
  0: All checksums verified successfully
  1: State file missing or invalid
  2: Checksum mismatches found
  3: Missing checksum entries for data files
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / 'state' / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml'
DATA_RAW_PATH = PROJECT_ROOT / 'data' / 'raw'

# Expected state file structure
EXPECTED_KEYS = {
    'project_id',
    'created_at',
    'last_updated',
    'checksums'
}

def compute_file_checksum_sha256(file_path: Path) -> Optional[str]:
    """Compute SHA256 checksum for a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return None

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
        return 0

def get_file_modified_time(file_path: Path) -> str:
    """Get file modified time as ISO string."""
    try:
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).isoformat()
    except Exception as e:
        logger.error(f"Failed to get modified time for {file_path}: {e}")
        return ""

def find_data_files(data_dir: Path) -> List[Path]:
    """Find all data files in the data directory."""
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []

    data_files = []
    for ext in ['*.csv', '*.json', '*.parquet', '*.txt', '*.gz', '*.zip']:
        data_files.extend(data_dir.rglob(ext))

    return sorted(data_files)

def load_state_file(state_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse the state YAML file."""
    if not state_path.exists():
        logger.error(f"State file does not exist: {state_path}")
        return None

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f)
            return state if isinstance(state, dict) else None
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file YAML: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to read state file: {e}")
        return None

def save_state_file(state_path: Path, state: Dict[str, Any]) -> bool:
    """Save state dictionary to YAML file."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=True)
        return True
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        return False

def verify_checksum_entry(
    state_checksums: Dict[str, Any],
    file_path: Path,
    relative_path: str
) -> Tuple[bool, Optional[str]]:
    """
    Verify a single checksum entry against the actual file.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if relative_path not in state_checksums:
        return False, f"Missing checksum entry for {relative_path}"

    entry = state_checksums[relative_path]
    actual_checksum = compute_file_checksum_sha256(file_path)

    if actual_checksum is None:
        return False, f"Failed to compute checksum for {relative_path}"

    stored_checksum = entry.get('checksum_sha256')
    if stored_checksum != actual_checksum:
        return False, f"Checksum mismatch for {relative_path}: expected {stored_checksum}, got {actual_checksum}"

    # Verify file size
    actual_size = get_file_size(file_path)
    stored_size = entry.get('size_bytes')
    if stored_size != actual_size:
        logger.warning(f"Size mismatch for {relative_path}: expected {stored_size}, got {actual_size}")

    return True, None

def verify_state_checksums() -> int:
    """
    Main verification routine.

    Returns:
        Exit code (0=success, 1-3=various failures)
    """
    exit_code = 0

    # Step 1: Verify state file exists
    if not STATE_FILE_PATH.exists():
        logger.error(f"State file missing: {STATE_FILE_PATH}")
        logger.info("Run code/scripts/generate_data_checksums.py to create the state file")
        return 1

    # Step 2: Load state file
    state = load_state_file(STATE_FILE_PATH)
    if state is None:
        logger.error("Failed to load state file")
        return 1

    # Step 3: Verify required keys exist
    missing_keys = EXPECTED_KEYS - set(state.keys())
    if missing_keys:
        logger.error(f"State file missing required keys: {missing_keys}")
        exit_code = 1

    # Step 4: Find all data files
    data_files = find_data_files(DATA_RAW_PATH)
    logger.info(f"Found {len(data_files)} data files in {DATA_RAW_PATH}")

    if len(data_files) == 0:
        logger.warning("No data files found to verify")
        return exit_code if exit_code != 0 else 0

    # Step 5: Get existing checksum entries
    state_checksums = state.get('checksums', {})
    if not isinstance(state_checksums, dict):
        logger.error("State file checksums section is not a dictionary")
        return 1

    # Step 6: Verify each data file has a checksum entry
    verified_count = 0
    mismatch_count = 0
    missing_count = 0
    verification_results = []

    for file_path in data_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        is_valid, error_msg = verify_checksum_entry(state_checksums, file_path, relative_path)

        if is_valid:
            verified_count += 1
            verification_results.append({
                'file': relative_path,
                'status': 'VERIFIED',
                'error': None
            })
            logger.info(f"✓ Verified: {relative_path}")
        else:
            if "Missing checksum entry" in error_msg:
                missing_count += 1
                exit_code = max(exit_code, 3)
            else:
                mismatch_count += 1
                exit_code = max(exit_code, 2)

            verification_results.append({
                'file': relative_path,
                'status': 'FAILED',
                'error': error_msg
            })
            logger.error(f"✗ Failed: {relative_path} - {error_msg}")

    # Step 7: Check for extra entries in state file (optional warning)
    data_file_paths = {str(f.relative_to(PROJECT_ROOT)) for f in data_files}
    extra_entries = set(state_checksums.keys()) - data_file_paths
    if extra_entries:
        logger.warning(f"State file has {len(extra_entries)} extra checksum entries for files no longer present")

    # Step 8: Print summary
    logger.info("=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total data files found: {len(data_files)}")
    logger.info(f"Checksums verified: {verified_count}")
    logger.info(f"Checksum mismatches: {mismatch_count}")
    logger.info(f"Missing checksum entries: {missing_count}")
    logger.info(f"Extra state entries: {len(extra_entries)}")
    logger.info("=" * 60)

    if exit_code == 0:
        logger.info("✓ All checksums verified successfully")
    elif exit_code == 2:
        logger.error("✗ Checksum mismatches detected - files may have been modified")
    elif exit_code == 3:
        logger.error("✗ Missing checksum entries - run generate_data_checksums.py to update")

    return exit_code

def main():
    """Entry point for the verification script."""
    logger.info("Starting state checksum verification...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"State file: {STATE_FILE_PATH}")
    logger.info(f"Data directory: {DATA_RAW_PATH}")
    logger.info("")

    exit_code = verify_state_checksums()

    logger.info("")
    logger.info(f"Verification completed with exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
