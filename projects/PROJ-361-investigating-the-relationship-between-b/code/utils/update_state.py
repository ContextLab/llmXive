"""
State tracking and versioning utilities for the llmXive pipeline.
Implements Constitution Principle V: Versioning and Hash Tracking.

This module provides functions to:
- Calculate file hashes for integrity verification
- Register artifacts in the SQLite metadata registry
- Track pipeline state across execution stages
- Trigger state updates from pre-commit hooks
"""

import hashlib
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

# Import database utilities
# Note: We use a relative import pattern that works when run as a script or module
try:
    from utils.db_schema import get_schema, init_db, register_file, update_file_status, calculate_file_hash as db_calculate_hash
except ImportError:
    # Fallback for direct execution without package structure
    import sqlite3
    from pathlib import Path

    def init_db(db_path: str) -> sqlite3.Connection:
        """Initialize the SQLite database with the required schema."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create subjects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Create files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id TEXT,
                file_path TEXT NOT NULL,
                checksum TEXT,
                status TEXT DEFAULT 'pending',
                file_type TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
        ''')
        
        conn.commit()
        return conn

    def get_schema() -> Dict[str, Any]:
        """Return the database schema definition."""
        return {
            "tables": {
                "subjects": ["subject_id", "created_at", "status"],
                "files": ["file_id", "subject_id", "file_path", "checksum", "status", "file_type", "created_at", "updated_at"]
            }
        }

    def register_file(conn: sqlite3.Connection, subject_id: str, file_path: str, checksum: str, file_type: str = "artifact") -> int:
        """Register a new file in the database."""
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO files (subject_id, file_path, checksum, status, file_type, created_at, updated_at)
            VALUES (?, ?, ?, 'registered', ?, ?, ?)
        ''', (subject_id, file_path, checksum, file_type, now, now))
        conn.commit()
        return cursor.lastrowid

    def update_file_status(conn: sqlite3.Connection, file_path: str, status: str, checksum: Optional[str] = None) -> bool:
        """Update the status of a file."""
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        if checksum:
            cursor.execute('''
                UPDATE files SET status = ?, checksum = ?, updated_at = ? WHERE file_path = ?
            ''', (status, checksum, now, file_path))
        else:
            cursor.execute('''
                UPDATE files SET status = ?, updated_at = ? WHERE file_path = ?
            ''', (status, now, file_path))
        conn.commit()
        return cursor.rowcount > 0

    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_project_root() -> Path:
        """Get the project root directory."""
        # Try to find .git directory
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / ".git").exists():
                return current
            current = current.parent
        # Fallback to parent of utils
        return Path(__file__).resolve().parent.parent.parent

    def get_db_path() -> Path:
        """Get the path to the SQLite database."""
        return get_project_root() / "data" / "metadata.db"

    def ensure_directories():
        """Ensure required directories exist."""
        db_path = get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent

def get_db_path() -> Path:
    """Get the path to the SQLite database."""
    return get_project_root() / "data" / "metadata.db"

def calculate_file_hash(file_path: str) -> str:
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
        "path": str(file_path),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "extension": file_path.suffix,
        "name": file_path.name
    }

def register_artifact(file_path: Path, subject_id: Optional[str] = None, file_type: str = "artifact") -> Dict[str, Any]:
    """Register an artifact in the metadata registry."""
    db_path = get_db_path()
    ensure_directories()
    conn = init_db(str(db_path))
    
    try:
        checksum = calculate_file_hash(str(file_path))
        rel_path = str(file_path.relative_to(get_project_root()))
        
        if subject_id is None:
            # Try to extract subject_id from path pattern sub-*/...
            parts = rel_path.split("/")
            for i, part in enumerate(parts):
                if part.startswith("sub-"):
                    subject_id = part
                    break
            if subject_id is None:
                subject_id = "global"
        
        file_id = register_file(conn, subject_id, rel_path, checksum, file_type)
        metadata = get_file_metadata(file_path)
        
        return {
            "success": True,
            "file_id": file_id,
            "subject_id": subject_id,
            "checksum": checksum,
            "metadata": metadata
        }
    finally:
        conn.close()

def update_artifact_status(file_path: Path, status: str, checksum: Optional[str] = None) -> bool:
    """Update the status of a registered artifact."""
    db_path = get_db_path()
    conn = init_db(str(db_path))
    
    try:
        rel_path = str(file_path.relative_to(get_project_root()))
        if checksum is None:
            checksum = calculate_file_hash(str(file_path))
        
        return update_file_status(conn, rel_path, status, checksum)
    finally:
        conn.close()

def verify_artifact_integrity(file_path: Path) -> bool:
    """Verify that a file's current hash matches its registered hash."""
    db_path = get_db_path()
    conn = init_db(str(db_path))
    
    try:
        cursor = conn.cursor()
        rel_path = str(file_path.relative_to(get_project_root()))
        
        cursor.execute("SELECT checksum FROM files WHERE file_path = ?", (rel_path,))
        result = cursor.fetchone()
        
        if not result:
            print(f"WARNING: File {rel_path} not found in registry")
            return False
        
        registered_hash = result[0]
        current_hash = calculate_file_hash(str(file_path))
        
        return registered_hash == current_hash
    finally:
        conn.close()

def get_pipeline_state() -> Dict[str, Any]:
    """Get the current state of the pipeline from the database."""
    db_path = get_db_path()
    conn = init_db(str(db_path))
    
    try:
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute("SELECT status, COUNT(*) FROM files GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]
        
        return {
            "subjects": subject_count,
            "files": status_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        conn.close()

def main():
    """Main entry point for pre-commit hook execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update artifact state tracking")
    parser.add_argument("--mode", choices=["pre-commit", "full-scan"], default="pre-commit",
                      help="Mode of operation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    project_root = get_project_root()
    db_path = get_db_path()
    
    if args.verbose:
        print(f"Project root: {project_root}")
        print(f"Database path: {db_path}")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize database
    conn = init_db(str(db_path))
    conn.close()
    
    if args.mode == "pre-commit":
        # Process staged files
        import subprocess
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True, text=True, check=True, cwd=project_root
            )
            staged_files = result.stdout.strip().split("\n")
            staged_files = [f for f in staged_files if f]
            
            if args.verbose:
                print(f"Staged files: {staged_files}")
            
            processed = 0
            for file_str in staged_files:
                file_path = project_root / file_str
                if file_path.exists() and file_path.is_file():
                    # Only process relevant directories
                    rel_path = file_path.relative_to(project_root)
                    if any(str(rel_path).startswith(d) for d in ["code/", "data/", "tests/", "specs/"]):
                        try:
                            result = register_artifact(file_path)
                            if args.verbose:
                                print(f"Registered: {file_str} (ID: {result['file_id']}, Hash: {result['checksum'][:16]}...)")
                            processed += 1
                        except Exception as e:
                            print(f"ERROR registering {file_str}: {e}")
            
            print(f"Processed {processed} staged artifacts")
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Could not get staged files: {e}")
            sys.exit(1)
    
    elif args.mode == "full-scan":
        # Scan all files in relevant directories
        relevant_dirs = ["code", "data", "tests", "specs"]
        processed = 0
        
        for dir_name in relevant_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            result = register_artifact(file_path)
                            if args.verbose:
                                print(f"Registered: {file_path.relative_to(project_root)}")
                            processed += 1
                        except Exception as e:
                            print(f"ERROR registering {file_path}: {e}")
        
        print(f"Full scan complete: {processed} artifacts processed")
    
    # Print pipeline state summary
    state = get_pipeline_state()
    print(f"Pipeline state: {json.dumps(state, indent=2)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())