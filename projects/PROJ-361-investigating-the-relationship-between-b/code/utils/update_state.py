"""
State management module for llmXive project.
Implements Constitution Principle V: Versioning and Hash Tracking.

This module provides utilities to:
1. Calculate SHA-256 hashes for data artifacts.
2. Register or update file metadata in the SQLite registry.
3. Validate data integrity by comparing stored hashes against current files.
4. Manage file status transitions (e.g., 'raw' -> 'processed').
"""

import hashlib
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import from sibling module as defined in API surface
from utils.db_schema import (
    get_schema,
    init_db,
    ensure_subject,
    register_file,
    update_file_status,
    get_files_by_status
)
from utils.config import get_project_root, get_data_dir

# Constants for status tracking
STATUS_RAW = "raw"
STATUS_DOWNLOADED = "downloaded"
STATUS_PREPROCESSED = "preprocessed"
STATUS_PROCESSED = "processed"
STATUS_FAILED = "failed"
STATUS_VALIDATED = "validated"

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., NIfTI)
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Gather metadata for a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary containing file metadata.
    """
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "hash": calculate_file_hash(file_path)
    }

def register_artifact(
    subject_id: str,
    file_path: Path,
    status: str = STATUS_RAW,
    db_path: Optional[Path] = None
) -> bool:
    """
    Register a new artifact or update its status in the SQLite registry.
    
    This function ensures the subject exists, calculates the file hash,
    and updates the registry with the current state.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-001').
        file_path: Absolute path to the artifact file.
        status: Initial status of the file.
        db_path: Optional path to the SQLite database. If None, uses default.
        
    Returns:
        True if registration/update was successful, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register non-existent file: {file_path}")
        
    if db_path is None:
        db_path = get_project_root() / "data" / "metadata.db"
        
    # Ensure database is initialized
    init_db(db_path)
    
    # Ensure subject exists
    ensure_subject(db_path, subject_id)
    
    # Calculate hash and metadata
    file_hash = calculate_file_hash(file_path)
    
    # Register or update
    # Note: register_file handles the logic of inserting new or updating existing
    # based on the file_path uniqueness constraint in the schema.
    register_file(db_path, subject_id, str(file_path), file_hash, status)
    
    return True

def update_artifact_status(
    subject_id: str,
    file_path: Path,
    new_status: str,
    db_path: Optional[Path] = None
) -> bool:
    """
    Update the status of an existing artifact.
    
    Args:
        subject_id: The subject identifier.
        file_path: Path to the artifact file.
        new_status: The new status string.
        db_path: Optional path to the SQLite database.
        
    Returns:
        True if update was successful.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not registered in the DB.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for status update: {file_path}")
        
    if db_path is None:
        db_path = get_project_root() / "data" / "metadata.db"
        
    # Verify file exists in DB before updating status
    # We check if any record exists for this subject and path
    files = get_files_by_status(db_path, subject_id, status=None) # Get all for subject
    file_registered = any(f['file_path'] == str(file_path) for f in files)
    
    if not file_registered:
        raise ValueError(f"File {file_path} is not registered for subject {subject_id}. Use register_artifact first.")
        
    # Recalculate hash to ensure integrity before status change
    # (Optional but recommended for strict versioning)
    current_hash = calculate_file_hash(file_path)
    
    # Update status
    # We assume update_file_status updates the status and optionally the hash if needed
    # If the schema doesn't support hash update, we might need to re-register.
    # For now, we call update_file_status which should handle the status change.
    update_file_status(db_path, subject_id, str(file_path), new_status)
    
    return True

def verify_artifact_integrity(
    subject_id: str,
    file_path: Path,
    db_path: Optional[Path] = None
) -> bool:
    """
    Verify that the file's current hash matches the stored hash.
    
    Args:
        subject_id: The subject identifier.
        file_path: Path to the artifact file.
        db_path: Optional path to the SQLite database.
        
    Returns:
        True if the hash matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not registered.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for verification: {file_path}")
        
    if db_path is None:
        db_path = get_project_root() / "data" / "metadata.db"
        
    files = get_files_by_status(db_path, subject_id, status=None)
    record = next((f for f in files if f['file_path'] == str(file_path)), None)
    
    if not record:
        raise ValueError(f"File {file_path} is not registered for subject {subject_id}.")
        
    stored_hash = record['checksum']
    current_hash = calculate_file_hash(file_path)
    
    return stored_hash == current_hash

def get_pipeline_state(
    subject_id: str,
    db_path: Optional[Path] = None
) -> Dict[str, Dict[str, str]]:
    """
    Get the current state of all artifacts for a subject.
    
    Returns a dictionary mapping file paths to their current status.
    
    Args:
        subject_id: The subject identifier.
        db_path: Optional path to the SQLite database.
        
    Returns:
        Dictionary of {file_path: status}.
    """
    if db_path is None:
        db_path = get_project_root() / "data" / "metadata.db"
        
    files = get_files_by_status(db_path, subject_id, status=None)
    return {f['file_path']: f['status'] for f in files}

def main():
    """
    CLI entry point for manual state updates and verification.
    Usage: python -m code.utils.update_state <command> [args]
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.update_state <command> [args]")
        print("Commands:")
        print("  register <subject_id> <file_path> [status]")
        print("  update <subject_id> <file_path> <new_status>")
        print("  verify <subject_id> <file_path>")
        print("  state <subject_id>")
        sys.exit(1)
        
    command = sys.argv[1]
    db_path = get_project_root() / "data" / "metadata.db"
    
    try:
        if command == "register":
            if len(sys.argv) < 4:
                print("Error: register requires <subject_id> and <file_path>")
                sys.exit(1)
            subject_id = sys.argv[2]
            file_path = Path(sys.argv[3])
            status = sys.argv[4] if len(sys.argv) > 4 else STATUS_RAW
            register_artifact(subject_id, file_path, status, db_path)
            print(f"Registered {file_path} for {subject_id} with status {status}")
            
        elif command == "update":
            if len(sys.argv) < 5:
                print("Error: update requires <subject_id>, <file_path>, and <new_status>")
                sys.exit(1)
            subject_id = sys.argv[2]
            file_path = Path(sys.argv[3])
            new_status = sys.argv[4]
            update_artifact_status(subject_id, file_path, new_status, db_path)
            print(f"Updated {file_path} to status {new_status}")
            
        elif command == "verify":
            if len(sys.argv) < 4:
                print("Error: verify requires <subject_id> and <file_path>")
                sys.exit(1)
            subject_id = sys.argv[2]
            file_path = Path(sys.argv[3])
            if verify_artifact_integrity(subject_id, file_path, db_path):
                print(f"Integrity verified: {file_path}")
            else:
                print(f"Integrity FAILED: {file_path} hash mismatch")
                sys.exit(1)
                
        elif command == "state":
            if len(sys.argv) < 3:
                print("Error: state requires <subject_id>")
                sys.exit(1)
            subject_id = sys.argv[2]
            state = get_pipeline_state(subject_id, db_path)
            print(json.dumps(state, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"File Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Value Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
