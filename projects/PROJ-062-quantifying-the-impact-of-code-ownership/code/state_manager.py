"""
State Manager for Code Ownership Analysis Project.

Handles content hashing, versioning, and state tracking for ownership metrics.
Implements Constitution Principle VI: raw ownership attribution CSVs MUST be
version-controlled and included in the repository.
"""

import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
OWNERSHIP_METRICS_DIR = PROJECT_ROOT / "data" / "ownership_metrics"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
OWNERSHIP_METRICS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise

def get_ownership_csv_files() -> List[Path]:
    """
    Get all ownership CSV files in the ownership_metrics directory.

    Returns:
        List of Path objects for CSV files matching *_ownership.csv pattern
    """
    if not OWNERSHIP_METRICS_DIR.exists():
        logger.warning(f"Ownership metrics directory does not exist: {OWNERSHIP_METRICS_DIR}")
        return []

    csv_files = list(OWNERSHIP_METRICS_DIR.glob("*_ownership.csv"))
    logger.info(f"Found {len(csv_files)} ownership CSV files")
    return csv_files

def generate_state_snapshot() -> Dict[str, Any]:
    """
    Generate a state snapshot containing hashes and metadata for all ownership CSVs.

    Returns:
        Dictionary containing state snapshot data
    """
    csv_files = get_ownership_csv_files()
    
    if not csv_files:
        logger.warning("No ownership CSV files found to snapshot")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "files": [],
            "total_files": 0,
            "status": "empty"
        }

    file_states = []
    for csv_file in csv_files:
        try:
            file_hash = calculate_file_hash(csv_file)
            file_size = csv_file.stat().st_size
            modified_time = datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat()
            
            file_state = {
                "filename": csv_file.name,
                "relative_path": str(csv_file.relative_to(PROJECT_ROOT)),
                "hash": file_hash,
                "size_bytes": file_size,
                "last_modified": modified_time
            }
            file_states.append(file_state)
            logger.info(f"Hashed file: {csv_file.name} -> {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to process file {csv_file}: {e}")
            continue

    state_snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0",
        "files": file_states,
        "total_files": len(file_states),
        "status": "complete" if len(file_states) == len(csv_files) else "partial"
    }

    return state_snapshot

def save_state_snapshot(state_data: Dict[str, Any], snapshot_name: Optional[str] = None) -> Path:
    """
    Save state snapshot to a YAML file.

    Args:
        state_data: Dictionary containing state snapshot data
        snapshot_name: Optional name for the snapshot file (defaults to timestamp-based)

    Returns:
        Path to the saved snapshot file
    """
    if snapshot_name is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"state_{timestamp}.yaml"

    snapshot_path = STATE_DIR / snapshot_name

    try:
        with open(snapshot_path, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State snapshot saved to: {snapshot_path}")
        return snapshot_path
    except Exception as e:
        logger.error(f"Failed to save state snapshot: {e}")
        raise

def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify that a file's current hash matches the expected hash.

    Args:
        file_path: Path to the file to verify
        expected_hash: Expected SHA-256 hash

    Returns:
        True if hashes match, False otherwise
    """
    try:
        current_hash = calculate_file_hash(file_path)
        is_valid = current_hash == expected_hash
        if not is_valid:
            logger.warning(f"Hash mismatch for {file_path}: expected {expected_hash[:16]}..., got {current_hash[:16]}...")
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying file {file_path}: {e}")
        return False

def verify_state_snapshot(snapshot_path: Path) -> Dict[str, Any]:
    """
    Verify all files in a state snapshot against their recorded hashes.

    Args:
        snapshot_path: Path to the state snapshot YAML file

    Returns:
        Dictionary with verification results
    """
    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_path}: {e}")
        return {"status": "error", "message": str(e)}

    results = {
        "snapshot_path": str(snapshot_path),
        "files_checked": 0,
        "files_valid": 0,
        "files_invalid": 0,
        "files_missing": 0,
        "details": []
    }

    for file_info in snapshot_data.get("files", []):
        relative_path = file_info.get("relative_path")
        expected_hash = file_info.get("hash")
        filename = file_info.get("filename")
        
        results["files_checked"] += 1
        
        if not relative_path:
            results["files_missing"] += 1
            results["details"].append({
                "file": filename,
                "status": "missing_path",
                "message": "No relative_path in snapshot"
            })
            continue

        full_path = PROJECT_ROOT / relative_path

        if not full_path.exists():
            results["files_missing"] += 1
            results["details"].append({
                "file": filename,
                "status": "missing",
                "message": f"File not found at {full_path}"
            })
            continue

        is_valid = verify_file_integrity(full_path, expected_hash)
        if is_valid:
            results["files_valid"] += 1
            results["details"].append({
                "file": filename,
                "status": "valid",
                "hash": expected_hash[:16] + "..."
            })
        else:
            results["files_invalid"] += 1
            results["details"].append({
                "file": filename,
                "status": "invalid",
                "message": "Hash mismatch"
            })

    results["status"] = "complete" if results["files_invalid"] == 0 and results["files_missing"] == 0 else "incomplete"
    return results

def update_gitignore() -> None:
    """
    Update .gitignore to explicitly ignore raw/intermediate data while allowing ownership_metrics CSVs.
    
    This implements the specific deviation from the Plan's 'Versioning Discipline':
    - Aggregated ownership metrics (CSVs in data/ownership_metrics/) ARE committed
    - Raw git data (data/raw/) and intermediate data (data/intermediate/) are NOT committed
    """
    gitignore_path = PROJECT_ROOT / ".gitignore"
    
    required_entries = [
        "# Data directories (raw and intermediate are not versioned)",
        "data/raw/",
        "data/intermediate/",
        "",
        "# Exception: Ownership metrics CSVs MUST be versioned (Constitution Principle VI)",
        "!data/ownership_metrics/*.csv",
    ]
    
    current_entries = []
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            current_entries = f.read().splitlines()
    
    # Check if entries already exist
    existing_patterns = set()
    for entry in current_entries:
        stripped = entry.strip()
        if stripped:
            existing_patterns.add(stripped)
    
    new_entries = []
    added = set()
    
    for entry in required_entries:
        stripped = entry.strip()
        if stripped and stripped not in existing_patterns and stripped not in added:
            new_entries.append(entry)
            added.add(stripped)
    
    if new_entries:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write("\n".join(new_entries))
            f.write("\n")
        logger.info(f"Updated .gitignore with {len(new_entries)} new entries")
    else:
        logger.info(".gitignore already contains required entries")

def generate_latest_snapshot() -> Path:
    """
    Generate and save the latest state snapshot.
    
    Returns:
        Path to the generated snapshot file
    """
    logger.info("Generating latest state snapshot...")
    state_data = generate_state_snapshot()
    snapshot_path = save_state_snapshot(state_data)
    logger.info(f"State snapshot generated: {snapshot_path}")
    return snapshot_path

def main():
    """
    Main entry point for state management tasks.
    """
    logger.info("Starting State Manager...")
    
    # Update .gitignore to ensure proper versioning rules
    update_gitignore()
    
    # Generate latest snapshot
    snapshot_path = generate_latest_snapshot()
    
    # Verify the snapshot
    verification_results = verify_state_snapshot(snapshot_path)
    
    logger.info(f"Verification status: {verification_results['status']}")
    logger.info(f"Files checked: {verification_results['files_checked']}")
    logger.info(f"Files valid: {verification_results['files_valid']}")
    logger.info(f"Files invalid: {verification_results['files_invalid']}")
    logger.info(f"Files missing: {verification_results['files_missing']}")
    
    return verification_results

if __name__ == "__main__":
    main()
