"""
Post-run artifact hashing and state updates.

This module provides utilities to compute file hashes, scan artifact directories,
and maintain a manifest of the project state after simulation runs.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.config import Config


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default 'sha256').
        
    Returns:
        Hexadecimal digest of the file hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()


def get_git_commit_hash() -> Optional[str]:
    """
    Retrieve the current git commit hash.
    
    Returns:
        Short git commit hash (7 characters) or None if not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def scan_artifacts(
    base_dir: str,
    extensions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan a directory recursively for artifacts and compute their metadata.
    
    Args:
        base_dir: Root directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, includes all files.
                    
    Returns:
        List of dictionaries containing file metadata (path, size, hash, modified_time).
    """
    artifacts = []
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return artifacts
        
    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue
                    
            try:
                stat_info = file_path.stat()
                file_hash = compute_file_hash(str(file_path))
                
                artifacts.append({
                    "path": str(file_path.relative_to(base_path)),
                    "absolute_path": str(file_path),
                    "size_bytes": stat_info.st_size,
                    "hash_sha256": file_hash,
                    "modified_time": datetime.fromtimestamp(
                        stat_info.st_mtime
                    ).isoformat(),
                    "extension": file_path.suffix
                })
            except (OSError, ValueError) as e:
                # Log warning but continue scanning
                print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)
                
    return artifacts


def update_state_manifest(
    output_path: str,
    artifacts: List[Dict[str, Any]],
    git_hash: Optional[str] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create or update a JSON manifest file with the current state of artifacts.
    
    Args:
        output_path: Path where the manifest JSON file will be written.
        artifacts: List of artifact metadata dictionaries from scan_artifacts.
        git_hash: Current git commit hash.
        additional_metadata: Optional dictionary of extra metadata to include.
        
    Returns:
        Path to the written manifest file.
    """
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "git_commit": git_hash,
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
        "metadata": additional_metadata or {}
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to a temporary file first, then rename for atomicity
    temp_path = output_file.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
        
    os.replace(temp_path, output_file)
    
    return str(output_file)


def verify_state_integrity(
    manifest_path: str,
    base_dir: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Verify that artifacts listed in a manifest match their current state on disk.
    
    Args:
        manifest_path: Path to the state manifest JSON file.
        base_dir: Optional base directory for relative path resolution.
                  If None, uses paths as stored in the manifest.
                  
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    if not os.path.exists(manifest_path):
        return False, [f"Manifest file not found: {manifest_path}"]
        
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in manifest: {e}"]
        
    artifacts = manifest.get("artifacts", [])
    
    for artifact in artifacts:
        file_path = artifact.get("path")
        if not file_path:
            errors.append("Artifact missing 'path' field")
            continue
            
        full_path = os.path.join(base_dir, file_path) if base_dir else file_path
        
        if not os.path.exists(full_path):
            errors.append(f"Artifact missing on disk: {file_path}")
            continue
            
        try:
            current_hash = compute_file_hash(full_path)
            stored_hash = artifact.get("hash_sha256")
            
            if current_hash != stored_hash:
                errors.append(
                    f"Hash mismatch for {file_path}: "
                    f"expected {stored_hash}, got {current_hash}"
                )
        except Exception as e:
            errors.append(f"Error verifying {file_path}: {e}")
            
    return len(errors) == 0, errors


def main() -> int:
    """
    CLI entry point for updating and verifying project state.
    
    Usage:
        python -m code.utils.update_state [--scan <dir>] [--output <path>] [--verify <manifest>]
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update and verify project artifact state"
    )
    parser.add_argument(
        "--scan",
        type=str,
        default="artifacts",
        help="Directory to scan for artifacts (default: artifacts)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/state_manifest.json",
        help="Path to write the state manifest (default: artifacts/state_manifest.json)"
    )
    parser.add_argument(
        "--verify",
        type=str,
        help="Path to an existing manifest to verify instead of creating a new one"
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=[".csv", ".json", ".png", ".txt"],
        help="File extensions to include in the scan"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        # Verification mode
        print(f"Verifying state integrity for: {args.verify}")
        is_valid, errors = verify_state_integrity(args.verify)
        
        if is_valid:
            print("✓ State integrity verified successfully.")
            return 0
        else:
            print("✗ State integrity check failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
    else:
        # Scan and update mode
        print(f"Scanning directory: {args.scan}")
        artifacts = scan_artifacts(args.scan, extensions=args.extensions)
        
        if not artifacts:
            print("No artifacts found to scan.")
            return 1
            
        git_hash = get_git_commit_hash()
        print(f"Git commit: {git_hash or 'Not in a git repository'}")
        
        print(f"Writing manifest to: {args.output}")
        manifest_path = update_state_manifest(
            args.output,
            artifacts,
            git_hash=git_hash,
            additional_metadata={
                "scan_directory": args.scan,
                "extensions_scanned": args.extensions,
                "total_files": len(artifacts)
            }
        )
        
        print(f"✓ Successfully updated state manifest with {len(artifacts)} artifacts.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
