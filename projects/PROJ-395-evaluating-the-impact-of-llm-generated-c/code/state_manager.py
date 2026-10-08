"""
State versioning logic for llmXive pipeline.

Computes and records SHA-256 hashes for project artifacts to ensure
reproducibility and traceability (Constitution Principle VII).
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import shared config if available, otherwise define defaults
try:
    import config
    STATE_DIR = Path(config.STATE_DIR) if hasattr(config, 'STATE_DIR') else Path("state")
except ImportError:
    STATE_DIR = Path("state")

# Ensure state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
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
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def hash_directory(
    dir_path: Path,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory.
    
    Args:
        dir_path: Path to the directory to hash.
        extensions: Optional list of file extensions to include (e.g., ['.py', '.csv']).
        exclude_patterns: Optional list of glob patterns to exclude (e.g., ['__pycache__', '*.log']).
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    hashes = {}
    exclude_set = set(exclude_patterns or [])
    
    for root, dirs, files in os.walk(dir_path):
        # Filter directories to exclude
        dirs[:] = [d for d in dirs if not any(
            Path(root, d).match(pattern) for pattern in exclude_patterns or []
        )]
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(dir_path)
            
            # Check extensions filter
            if extensions and file_path.suffix not in extensions:
                continue
            
            # Check exclude patterns
            if any(str(rel_path).match(pattern) for pattern in exclude_patterns or []):
                continue
            
            try:
                hashes[str(rel_path)] = compute_sha256(file_path)
            except (FileNotFoundError, IOError) as e:
                # Log warning but continue
                print(f"Warning: Could not hash {rel_path}: {e}")
    
    return hashes


def record_state_snapshot(
    artifacts: List[Path],
    output_file: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Record a snapshot of artifact hashes with metadata.
    
    Args:
        artifacts: List of file paths to include in the snapshot.
        output_file: Optional path for the output JSON file. Defaults to 
                    `state/snapshot_YYYYMMDD_HHMMSS.json`.
        metadata: Optional dictionary of additional metadata to include.
                
    Returns:
        Path to the created snapshot file.
    """
    if not artifacts:
        raise ValueError("At least one artifact path must be provided")
    
    # Validate all paths exist
    for artifact in artifacts:
        if not artifact.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact}")
    
    # Generate default output path
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = STATE_DIR / f"snapshot_{timestamp}.json"
    
    # Build snapshot data
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "artifacts": {},
        "metadata": metadata or {}
    }
    
    for artifact in artifacts:
        try:
            rel_path = artifact.relative_to(Path.cwd())
        except ValueError:
            # Use absolute path if not relative to cwd
            rel_path = artifact
        
        snapshot["artifacts"][str(rel_path)] = {
            "hash": compute_sha256(artifact),
            "size_bytes": artifact.stat().st_size,
            "last_modified": datetime.fromtimestamp(
                artifact.stat().st_mtime
            ).isoformat()
        }
    
    # Write snapshot to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    
    return output_file


def verify_snapshot(
    snapshot_file: Path,
    base_dir: Optional[Path] = None
) -> Dict[str, bool]:
    """
    Verify that artifacts match a previously recorded snapshot.
    
    Args:
        snapshot_file: Path to the snapshot JSON file.
        base_dir: Base directory for relative paths in snapshot. 
                 Defaults to current working directory.
                
    Returns:
        Dictionary mapping artifact paths to verification status (True/False).
    """
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
    
    if base_dir is None:
        base_dir = Path.cwd()
    
    # Load snapshot
    with open(snapshot_file, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    
    verification_results = {}
    
    for rel_path, artifact_info in snapshot.get("artifacts", {}).items():
        expected_hash = artifact_info["hash"]
        file_path = base_dir / rel_path
        
        if not file_path.exists():
            verification_results[rel_path] = False
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            verification_results[rel_path] = (actual_hash == expected_hash)
        except (FileNotFoundError, IOError):
            verification_results[rel_path] = False
    
    return verification_results


def get_latest_snapshot() -> Optional[Path]:
    """
    Get the path to the most recent state snapshot.
    
    Returns:
        Path to the latest snapshot file, or None if no snapshots exist.
    """
    if not STATE_DIR.exists():
        return None
    
    snapshots = list(STATE_DIR.glob("snapshot_*.json"))
    if not snapshots:
        return None
    
    # Sort by filename (which includes timestamp)
    snapshots.sort(key=lambda p: p.name)
    return snapshots[-1]


def main():
    """
    Command-line interface for state versioning operations.
    
    Usage:
        python -m code.state_manager snapshot <artifact1> [artifact2 ...]
        python -m code.state_manager verify <snapshot_file>
        python -m code.state_manager list
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.state_manager <command> [args...]")
        print("Commands:")
        print("  snapshot <artifact1> [artifact2 ...] - Record state snapshot")
        print("  verify <snapshot_file>              - Verify artifacts against snapshot")
        print("  list                                - List available snapshots")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "snapshot":
        if len(sys.argv) < 3:
            print("Error: At least one artifact path required for snapshot")
            sys.exit(1)
        
        artifacts = [Path(arg) for arg in sys.argv[2:]]
        try:
            output = record_state_snapshot(artifacts)
            print(f"Snapshot recorded: {output}")
        except Exception as e:
            print(f"Error recording snapshot: {e}")
            sys.exit(1)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: Snapshot file path required for verification")
            sys.exit(1)
        
        snapshot_file = Path(sys.argv[2])
        try:
            results = verify_snapshot(snapshot_file)
            all_valid = all(results.values())
            
            print("Verification Results:")
            for path, valid in results.items():
                status = "✓" if valid else "✗"
                print(f"  {status} {path}")
            
            if not all_valid:
                print("Warning: Some artifacts failed verification")
                sys.exit(1)
            else:
                print("All artifacts verified successfully")
        except Exception as e:
            print(f"Error verifying snapshot: {e}")
            sys.exit(1)
    
    elif command == "list":
        snapshots = list(STATE_DIR.glob("snapshot_*.json"))
        if not snapshots:
            print("No snapshots found")
        else:
            print("Available snapshots:")
            for snapshot in sorted(snapshots):
                print(f"  {snapshot.name}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
