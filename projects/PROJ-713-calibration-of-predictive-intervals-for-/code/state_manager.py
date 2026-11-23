"""
State Manager: Verifies and tracks state hashes and updated_at timestamps.

This module implements the verification logic for the `state/` directory,
ensuring data integrity via SHA-256 checksums and temporal consistency
via `updated_at` timestamps.
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from utils.logger import get_logger
from utils.exceptions import DataValidationError, ConfigurationError

logger = get_logger(__name__)

# Constants
STATE_DIR_NAME = "state"
MANIFEST_FILENAME = "state_manifest.json"
HASH_ALGORITHM = "sha256"


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {file_path}") from e


def load_state_manifest(state_dir: Path) -> Dict[str, Any]:
    """
    Load the state manifest JSON file.
    
    Args:
        state_dir: Path to the state directory.
        
    Returns:
        Dictionary containing the manifest data.
        
    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    manifest_path = state_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"State manifest not found at {manifest_path}")
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in state manifest: {manifest_path}", e.doc, e.pos)
    except IOError as e:
        raise IOError(f"Failed to read state manifest: {manifest_path}") from e


def save_state_manifest(state_dir: Path, manifest_data: Dict[str, Any]) -> None:
    """
    Save the state manifest JSON file.
    
    Args:
        state_dir: Path to the state directory.
        manifest_data: Dictionary to save as JSON.
        
    Raises:
        IOError: If the file cannot be written.
    """
    manifest_path = state_dir / MANIFEST_FILENAME
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"State manifest saved to {manifest_path}")
    except IOError as e:
        raise IOError(f"Failed to write state manifest: {manifest_path}") from e


def verify_file_hash(state_dir: Path, file_rel_path: str, expected_hash: str) -> bool:
    """
    Verify the SHA-256 hash of a specific file in the state directory.
    
    Args:
        state_dir: Path to the state directory.
        file_rel_path: Relative path of the file within the state directory.
        expected_hash: Expected SHA-256 hash.
        
    Returns:
        True if the hash matches, False otherwise.
        
    Raises:
        DataValidationError: If the file is missing or the hash mismatch is critical.
    """
    full_path = state_dir / file_rel_path
    if not full_path.exists():
        logger.error(f"State file missing for hash verification: {full_path}")
        raise DataValidationError(f"State file missing: {file_rel_path}")
    
    try:
        actual_hash = compute_file_checksum(full_path)
    except Exception as e:
        logger.error(f"Error computing checksum for {full_path}: {e}")
        raise DataValidationError(f"Failed to compute checksum for {file_rel_path}") from e
    
    if actual_hash != expected_hash:
        logger.error(f"Hash mismatch for {file_rel_path}. Expected: {expected_hash}, Got: {actual_hash}")
        raise DataValidationError(
            f"Hash mismatch for state file '{file_rel_path}'. "
            f"Expected: {expected_hash}, Actual: {actual_hash}"
        )
    
    logger.debug(f"Hash verified for {file_rel_path}")
    return True


def verify_timestamps(state_dir: Path, manifest: Dict[str, Any]) -> List[str]:
    """
    Verify that timestamps in the manifest are consistent and valid.
    
    Checks:
    1. `updated_at` is a valid ISO 8601 string or Unix timestamp.
    2. `updated_at` is not in the future.
    3. If `files` is present, each file's `updated_at` matches the file's mtime.
    
    Args:
        state_dir: Path to the state directory.
        manifest: The loaded manifest dictionary.
        
    Returns:
        List of warning messages for any anomalies found (empty if all good).
    """
    warnings = []
    current_time = time.time()
    
    # Check root updated_at
    root_updated = manifest.get("updated_at")
    if root_updated:
        try:
            # Try parsing ISO format first
            dt = datetime.fromisoformat(root_updated.replace("Z", "+00:00"))
            ts = dt.timestamp()
        except ValueError:
            try:
                # Try parsing as float timestamp
                ts = float(root_updated)
            except (ValueError, TypeError):
                warnings.append(f"Invalid `updated_at` format in manifest: {root_updated}")
                return warnings
        
        if ts > current_time:
            warnings.append(f"`updated_at` in manifest is in the future: {root_updated}")
    
    # Check file-level timestamps
    files_info = manifest.get("files", {})
    for rel_path, file_info in files_info.items():
        file_ts = file_info.get("updated_at")
        if not file_ts:
            warnings.append(f"Missing `updated_at` for file in manifest: {rel_path}")
            continue
        
        full_path = state_dir / rel_path
        if full_path.exists():
            try:
                actual_mtime = full_path.stat().st_mtime
                # Allow small floating point drift
                if abs(actual_mtime - float(file_ts)) > 1.0:
                    warnings.append(
                        f"Mtime mismatch for {rel_path}. "
                        f"Manifest: {file_ts}, Filesystem: {actual_mtime}"
                    )
            except OSError as e:
                warnings.append(f"Cannot stat file {rel_path}: {e}")
        else:
            warnings.append(f"File listed in manifest but missing on disk: {rel_path}")
    
    return warnings


def verify_state_integrity(state_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Main verification entry point.
    
    Verifies:
    1. State directory exists.
    2. Manifest exists and is valid JSON.
    3. All files listed in manifest have correct SHA-256 hashes.
    4. Timestamps are consistent.
    
    Args:
        state_dir: Optional path override. Defaults to PROJECT_ROOT / "state".
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    from config import PROJECT_ROOT
    
    if state_dir is None:
        state_dir = PROJECT_ROOT / STATE_DIR_NAME
    
    errors = []
    warnings = []
    
    if not state_dir.exists():
        errors.append(f"State directory does not exist: {state_dir}")
        return False, errors
    
    try:
        manifest = load_state_manifest(state_dir)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        errors.append(f"Failed to load state manifest: {e}")
        return False, errors
    
    # Verify hashes
    files_info = manifest.get("files", {})
    for rel_path, file_info in files_info.items():
        expected_hash = file_info.get("hash")
        if not expected_hash:
            errors.append(f"Missing hash for {rel_path} in manifest")
            continue
        
        try:
            verify_file_hash(state_dir, rel_path, expected_hash)
        except DataValidationError as e:
            errors.append(str(e))
    
    # Verify timestamps
    timestamp_warnings = verify_timestamps(state_dir, manifest)
    warnings.extend(timestamp_warnings)
    
    all_warnings = errors + warnings
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("State integrity verification passed.")
    else:
        logger.error(f"State integrity verification failed with {len(errors)} errors and {len(warnings)} warnings.")
    
    return is_valid, all_warnings


def update_state_manifest(state_dir: Optional[Path] = None, files_to_add: Optional[List[Path]] = None) -> None:
    """
    Update the state manifest with current file hashes and timestamps.
    
    This is used to create or refresh the `state/` tracking after a pipeline run.
    
    Args:
        state_dir: Optional path override.
        files_to_add: List of file paths to include in the manifest.
    """
    from config import PROJECT_ROOT
    
    if state_dir is None:
        state_dir = PROJECT_ROOT / STATE_DIR_NAME
    
    if not state_dir.exists():
        logger.warning(f"State directory does not exist, creating: {state_dir}")
        state_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "version": "1.0",
        "files": {}
    }
    
    if files_to_add:
        for file_path in files_to_add:
            if not file_path.exists():
                logger.warning(f"Skipping missing file for state update: {file_path}")
                continue
            
            rel_path = str(file_path.relative_to(state_dir))
            file_hash = compute_file_checksum(file_path)
            mtime = file_path.stat().st_mtime
            
            manifest["files"][rel_path] = {
                "hash": file_hash,
                "updated_at": mtime,
                "size": file_path.stat().st_size
            }
    
    # Update the root timestamp
    manifest["updated_at"] = datetime.now().isoformat()
    
    save_state_manifest(state_dir, manifest)


def main():
    """CLI entry point for state verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify state hashes and timestamps.")
    parser.add_argument(
        "--state-dir",
        type=str,
        default=None,
        help="Path to the state directory (default: PROJECT_ROOT/state)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the manifest with current file states instead of verifying."
    )
    
    args = parser.parse_args()
    
    state_path = Path(args.state_dir) if args.state_dir else None
    
    try:
        if args.update:
            update_state_manifest(state_path)
            print("State manifest updated successfully.")
        else:
            is_valid, messages = verify_state_integrity(state_path)
            if is_valid:
                print("Verification PASSED.")
            else:
                print("Verification FAILED.")
            
            for msg in messages:
                print(f"  - {msg}")
                
            return 0 if is_valid else 1
    except Exception as e:
        logger.exception(f"Unexpected error during state operation: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
