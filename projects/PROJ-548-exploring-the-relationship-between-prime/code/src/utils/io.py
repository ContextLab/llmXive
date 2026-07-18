import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import yaml
import time
import json
from .config import get_project_paths

# Constants for state file
STATE_FILE_NAME = "PROJ-548-exploring-the-relationship-between-prime.yaml"
STATE_DIR = "state/projects"

def _get_state_path() -> Path:
    """Returns the full path to the project state YAML file."""
    base, _ = get_project_paths()
    return base / STATE_DIR / STATE_FILE_NAME

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
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
            # Read in chunks to handle large files memory efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def compute_directory_checksum(dir_path: Path, exclude_patterns: Optional[List[str]] = None) -> str:
    """
    Computes a deterministic checksum for a directory based on its files.
    
    This function hashes the sorted list of relative file paths and their 
    individual checksums to create a directory fingerprint.
    
    Args:
        dir_path: Path to the directory.
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.pyc', '__pycache__']).
        
    Returns:
        Hexadecimal string of the directory checksum.
    """
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    exclude_patterns = exclude_patterns or []
    
    def should_exclude(path: Path) -> bool:
        name = path.name
        return any(name.endswith(pat.lstrip('*')) for pat in exclude_patterns)

    file_hashes = []
    for root, _, files in os.walk(dir_path):
        for filename in sorted(files):
            if should_exclude(Path(filename)):
                continue
            file_path = Path(root) / filename
            try:
                rel_path = file_path.relative_to(dir_path)
                file_hash = compute_file_checksum(file_path)
                # Include relative path in hash to detect renames
                file_hashes.append(f"{rel_path}:{file_hash}")
            except Exception:
                continue
    
    combined = "\n".join(file_hashes)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Loads the project state from the YAML file.
    
    Returns:
        Dictionary containing the state data. Returns an empty dict if file doesn't exist.
    """
    state_path = _get_state_path()
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse state file {state_path}: {e}")

def save_state(data: Dict[str, Any]) -> None:
    """
    Saves the project state to the YAML file.
    
    Args:
        data: Dictionary to save.
    """
    state_path = _get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def update_state_checksums(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Updates the checksums in the state dictionary for key data artifacts.
    
    This implements Constitution Principle V by recording the cryptographic 
    fingerprint of processed data files to ensure data integrity and 
    reproducibility.
    
    Args:
        data: Optional existing state dictionary. If None, loads current state.
        
    Returns:
        Updated state dictionary with new checksums.
    """
    if data is None:
        data = load_state()
    
    if "checksums" not in data:
        data["checksums"] = {}
    
    # Define artifacts to checksum based on the project pipeline
    artifacts = {
        "primes_gaps": Path("data/processed/primes_gaps.csv"),
        "zeta_zeros": Path("data/processed/zeta_zeros.csv"),
        "results": Path("results/correlation_results.json"),
        "plot": Path("results/correlation_plot.png"),
        "robustness": Path("results/robustness_report.md"),
        "permutation": Path("results/permutation_test.json"),
    }
    
    base_dir, _ = get_project_paths()
    current_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    for key, rel_path in artifacts.items():
        full_path = base_dir / rel_path
        if full_path.exists():
            try:
                checksum = compute_file_checksum(full_path)
                data["checksums"][key] = {
                    "path": str(rel_path),
                    "sha256": checksum,
                    "updated_at": current_timestamp
                }
            except (FileNotFoundError, IOError) as e:
                # Log warning but continue, don't fail the whole update
                print(f"Warning: Could not checksum {rel_path}: {e}")
        else:
            # If file doesn't exist yet, remove old checksum if present
            if key in data["checksums"]:
                del data["checksums"][key]
    
    # Update the metadata for the state file itself
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["last_checksum_update"] = current_timestamp
    
    return data

def verify_data_integrity(data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, str]]:
    """
    Verifies the integrity of data artifacts against stored checksums.
    
    Args:
        data: Optional existing state dictionary.
        
    Returns:
        Tuple of (is_valid, details_dict). 
        is_valid is True if all checksums match.
        details_dict maps artifact keys to status messages.
    """
    if data is None:
        data = load_state()
    
    checksums = data.get("checksums", {})
    base_dir, _ = get_project_paths()
    results = {}
    all_valid = True
    
    for key, info in checksums.items():
        rel_path = info.get("path")
        stored_hash = info.get("sha256")
        
        if not rel_path or not stored_hash:
            results[key] = "Invalid state entry"
            all_valid = False
            continue
            
        full_path = base_dir / rel_path
        
        if not full_path.exists():
            results[key] = "File missing"
            all_valid = False
            continue
        
        try:
            current_hash = compute_file_checksum(full_path)
            if current_hash == stored_hash:
                results[key] = "Valid"
            else:
                results[key] = f"Corrupted (Expected: {stored_hash[:8]}..., Got: {current_hash[:8]}...)"
                all_valid = False
        except Exception as e:
            results[key] = f"Error verifying: {str(e)}"
            all_valid = False
            
    return all_valid, results

def get_data_change_summary(data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a human-readable summary of data integrity status.
    
    Args:
        data: Optional existing state dictionary.
        
    Returns:
        Formatted string report.
    """
    if data is None:
        data = load_state()
    
    is_valid, details = verify_data_integrity(data)
    lines = [
        f"Data Integrity Report (Generated: {time.strftime('%Y-%m-%d %H:%M:%S')})",
        "-" * 50,
        f"Overall Status: {'PASS' if is_valid else 'FAIL'}",
        ""
    ]
    
    for key, status in details.items():
        lines.append(f"  [{key}]: {status}")
        
    return "\n".join(lines)

# Convenience function to ensure the state file is updated after any data operation
def commit_state(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Updates checksums and saves the state file.
    
    This is the primary entry point for persisting integrity records.
    
    Args:
        data: Optional data to merge into state.
        
    Returns:
        The saved state dictionary.
    """
    current_state = load_state()
    if data:
        current_state.update(data)
    
    updated_state = update_state_checksums(current_state)
    save_state(updated_state)
    return updated_state
