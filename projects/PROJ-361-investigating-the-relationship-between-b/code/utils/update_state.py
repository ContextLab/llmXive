"""
State management module for llmXive pipeline.
Handles versioning, hash tracking, and artifact registration in SQLite metadata registry.
Implements Constitution Principle V: Track all changes to ensure reproducibility.
"""

import hashlib
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import sqlite3

# Import database schema functions
from utils.db_schema import (
    get_schema, 
    init_db, 
    ensure_subject, 
    register_file, 
    update_file_status, 
    get_files_by_status, 
    calculate_file_hash as db_calculate_hash
)

# Project root detection
def get_project_root() -> Path:
    """Detect project root by looking for .git directory or specific markers."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / '.git').exists() or (current / 'requirements.txt').exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = get_project_root()
DB_PATH = PROJECT_ROOT / 'data' / 'metadata.db'

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from a file."""
    stat = file_path.stat()
    return {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "absolute_path": str(file_path.resolve()),
        "relative_path": str(file_path.relative_to(PROJECT_ROOT)) if file_path.is_relative_to(PROJECT_ROOT) else str(file_path)
    }

def register_artifact(file_path: Path, file_hash: str, metadata: Dict[str, Any]) -> None:
    """
    Register a file as an artifact in the metadata registry.
    
    Args:
        file_path: Path to the file
        file_hash: SHA-256 hash of the file
        metadata: Dictionary of file metadata
    """
    # Ensure database is initialized
    init_db(DB_PATH)
    
    # Determine artifact type based on path
    relative_path = str(file_path.relative_to(PROJECT_ROOT)) if file_path.is_relative_to(PROJECT_ROOT) else str(file_path)
    
    if relative_path.startswith('code/'):
        artifact_type = 'code'
    elif relative_path.startswith('data/'):
        artifact_type = 'data'
    elif relative_path.startswith('tests/'):
        artifact_type = 'test'
    elif relative_path.startswith('specs/'):
        artifact_type = 'spec'
    else:
        artifact_type = 'config'
    
    # Register file in database
    register_file(
        file_path=str(relative_path),
        checksum=file_hash,
        status='registered',
        metadata=json.dumps(metadata),
        artifact_type=artifact_type
    )

def update_artifact_status(file_path: Path, status: str) -> None:
    """
    Update the status of an artifact in the registry.
    
    Args:
        file_path: Path to the file
        status: New status (e.g., 'staged', 'committed', 'modified')
    """
    relative_path = str(file_path.relative_to(PROJECT_ROOT)) if file_path.is_relative_to(PROJECT_ROOT) else str(file_path)
    update_file_status(relative_path, status)

def verify_artifact_integrity(file_path: Path) -> bool:
    """
    Verify that a file's current hash matches its registered hash.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if integrity verified, False otherwise
    """
    init_db(DB_PATH)
    
    relative_path = str(file_path.relative_to(PROJECT_ROOT)) if file_path.is_relative_to(PROJECT_ROOT) else str(file_path)
    
    # Get registered hash from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT checksum FROM files WHERE file_path = ?", (relative_path,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"File not registered in metadata: {relative_path}")
        return False
    
    registered_hash = result[0]
    current_hash = calculate_file_hash(file_path)
    
    return registered_hash == current_hash

def get_pipeline_state() -> Dict[str, Any]:
    """
    Get the current state of the pipeline by querying registered artifacts.
    
    Returns:
        Dictionary containing pipeline state information
    """
    init_db(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get counts by status
    cursor.execute("SELECT status, COUNT(*) FROM files GROUP BY status")
    status_counts = dict(cursor.fetchall())
    
    # Get counts by type
    cursor.execute("SELECT artifact_type, COUNT(*) FROM files GROUP BY artifact_type")
    type_counts = dict(cursor.fetchall())
    
    # Get recent modifications
    cursor.execute("""
        SELECT file_path, status, checksum 
        FROM files 
        ORDER BY modified DESC 
        LIMIT 10
    """)
    recent_files = cursor.fetchall()
    
    conn.close()
    
    return {
        "status_counts": status_counts,
        "type_counts": type_counts,
        "recent_files": [
            {"path": f[0], "status": f[1], "checksum": f[2]} 
            for f in recent_files
        ],
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main entry point for command-line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python update_state.py <command> [args]")
        print("Commands:")
        print("  verify <file_path>  - Verify file integrity")
        print("  state               - Show pipeline state")
        print("  register <file_path> - Register a file as artifact")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "verify":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        if verify_artifact_integrity(file_path):
            print(f"✓ Integrity verified: {file_path}")
        else:
            print(f"✗ Integrity check failed: {file_path}")
            sys.exit(1)
    
    elif command == "state":
        state = get_pipeline_state()
        print(json.dumps(state, indent=2))
    
    elif command == "register":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        metadata = get_file_metadata(file_path)
        file_hash = calculate_file_hash(file_path)
        register_artifact(file_path, file_hash, metadata)
        print(f"Registered: {file_path}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()