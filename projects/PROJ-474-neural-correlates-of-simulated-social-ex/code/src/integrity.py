import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json
import logging

from src.utils import get_logger, log_exception

class IntegrityError(Exception):
    """Custom exception for data integrity failures."""
    pass

def get_state_path() -> Path:
    """Returns the path to the project state YAML file."""
    # Project root is assumed to be the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent.parent
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "PROJ-474-neural-correlates-of-simulated-social-ex.yaml"

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default sha256).
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IntegrityError: If hash computation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files (e.g., NIfTI)
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        raise IntegrityError(f"Failed to compute hash for {file_path}: {e}")

def scan_data_directory(data_dir: Path, extensions: Optional[Set[str]] = None) -> List[Path]:
    """
    Scans a directory recursively for files.
    
    Args:
        data_dir: Root directory to scan.
        extensions: Optional set of extensions to filter (e.g., {'.nii', '.json'}).
                    If None, includes all files.
                    
    Returns:
        List of file paths.
    """
    if not data_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            f_path = Path(root) / filename
            if extensions is None or f_path.suffix.lower() in extensions:
                files.append(f_path)
    return files

def generate_hashes(data_dir: Path) -> Dict[str, str]:
    """
    Generates hashes for all files in the data directory.
    
    Args:
        data_dir: Path to the data directory.
        
    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    hashes = {}
    # Scan all common data extensions
    extensions = {'.nii', '.nii.gz', '.json', '.tsv', '.csv', '.txt', '.yaml', '.yml'}
    files = scan_data_directory(data_dir, extensions)
    
    logger = get_logger(__name__)
    logger.info(f"Scanning {len(files)} files in {data_dir}")
    
    for f_path in files:
        try:
            # Store relative path from data_dir
            rel_path = str(f_path.relative_to(data_dir))
            file_hash = compute_file_hash(f_path)
            hashes[rel_path] = file_hash
            logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
        except Exception as e:
            logger.warning(f"Skipping file {f_path} due to error: {e}")
            
    return hashes

def load_hashes(state_path: Path) -> Dict[str, str]:
    """
    Loads existing hashes from the state file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary of hashes, or empty dict if file missing/invalid.
    """
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f) or {}
            return data.get('artifact_hashes', {})
    except Exception as e:
        get_logger(__name__).warning(f"Could not load state file {state_path}: {e}")
        return {}

def save_hashes(hashes: Dict[str, str], state_path: Path) -> None:
    """
    Saves the hash dictionary to the state file.
    
    Args:
        hashes: Dictionary of relative_path -> hash.
        state_path: Path to the state YAML file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state to preserve other keys (like randomization_verified)
    existing_data = {}
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                existing_data = yaml.safe_load(f) or {}
        except Exception:
            pass
    
    existing_data['artifact_hashes'] = hashes
    
    with open(state_path, 'w') as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)

def verify_integrity(data_dir: Path, state_path: Optional[Path] = None) -> bool:
    """
    Verifies current data hashes against stored hashes.
    
    Args:
        data_dir: Path to the data directory.
        state_path: Path to the state file. Defaults to project default.
        
    Returns:
        True if integrity is verified, False otherwise.
        
    Raises:
        IntegrityError: If a mismatch is found.
    """
    if state_path is None:
        state_path = get_state_path()
        
    stored_hashes = load_hashes(state_path)
    current_hashes = generate_hashes(data_dir)
    
    if not stored_hashes:
        get_logger(__name__).info("No stored hashes found. Integrity check skipped (initial run).")
        return True
        
    # Check for missing files
    for rel_path, stored_hash in stored_hashes.items():
        full_path = data_dir / rel_path
        if not full_path.exists():
            raise IntegrityError(f"Missing artifact: {rel_path}")
        
        # Check hash match
        if rel_path in current_hashes:
            if current_hashes[rel_path] != stored_hash:
                raise IntegrityError(f"Hash mismatch for {rel_path}")
        else:
            # File exists but wasn't in the scan (shouldn't happen if extensions match)
            raise IntegrityError(f"Artifact {rel_path} found but not hashed in current scan.")
            
    # Check for new files not in stored (optional strictness)
    # For now, we assume new files are okay unless we want strict immutability.
    # Given the task is to store hashes, we primarily ensure existing tracked files haven't changed.
    
    return True

def update_hashes(data_dir: Path, state_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Scans the data directory, computes hashes, and updates the state file.
    
    Args:
        data_dir: Path to the data directory.
        state_path: Path to the state file. Defaults to project default.
        
    Returns:
        The updated dictionary of hashes.
    """
    if state_path is None:
        state_path = get_state_path()
        
    logger = get_logger(__name__)
    logger.info(f"Updating integrity hashes for {data_dir} -> {state_path}")
    
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Creating empty hash map.")
        hashes = {}
    else:
        hashes = generate_hashes(data_dir)
        
    save_hashes(hashes, state_path)
    logger.info(f"Successfully updated {len(hashes)} file hashes.")
    return hashes

def main():
    """CLI entry point for integrity updates."""
    logger = get_logger(__name__)
    logger.info("Running integrity check/update...")
    
    # Determine paths relative to script location
    script_dir = Path(__file__).resolve().parent.parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    try:
        update_hashes(data_dir)
        logger.info("Integrity update completed successfully.")
    except Exception as e:
        log_exception(e)
        raise

if __name__ == "__main__":
    main()
