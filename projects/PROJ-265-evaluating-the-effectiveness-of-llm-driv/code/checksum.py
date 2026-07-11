"""
Artifact versioning and integrity checking script.

Implements Constitution Principle V: All artifacts are versioned and 
their integrity is verifiable via checksums.

This script scans the project for artifacts, computes SHA-256 checksums,
and maintains a manifest file for version control and verification.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "state" / "artifact_manifest.json"
EXCLUDE_PATTERNS = {
    ".git",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.tmp",
    ".DS_Store",
    "venv",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    "code",
    "data",
    "results",
    "state",
    "specs",
    "tests",
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def should_exclude(file_path: Path) -> bool:
    """Check if a file or directory should be excluded from checksumming."""
    for part in file_path.parts:
        if part.startswith(".") and part not in {".", ".."}:
            if part in EXCLUDE_PATTERNS or part.startswith("."):
                # Allow hidden files that aren't cache/dotfiles
                if part not in {".gitignore", ".env.example"}:
                    return True
        if part in EXCLUDE_PATTERNS:
            return True
    if file_path.suffix in {".pyc", ".pyo", ".tmp"}:
        return True
    return False

def scan_directory(base_path: Path, relative_to: Path = None) -> List[Path]:
    """
    Recursively scan a directory for artifact files.
    
    Args:
        base_path: Directory to scan
        relative_to: Base path for relative path calculation (default: base_path)
        
    Returns:
        List of file paths that should be included
    """
    if relative_to is None:
        relative_to = base_path
        
    artifacts = []
    
    if not base_path.exists():
        return artifacts
        
    for item in base_path.rglob("*"):
        if item.is_file():
            if not should_exclude(item):
                artifacts.append(item)
                
    return artifacts

def save_checksum_manifest(checksums: Dict[str, str], metadata: Optional[Dict] = None) -> None:
    """
    Save checksums to the manifest file.
    
    Args:
        checksums: Dictionary of relative_path -> sha256_hash
        metadata: Optional metadata to include in the manifest
    """
    # Ensure state directory exists
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checksums": checksums,
    }
    
    if metadata:
        manifest["metadata"] = metadata
        
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def verify_checksums() -> Tuple[bool, List[str], List[str]]:
    """
    Verify all artifacts against the stored manifest.
    
    Returns:
        Tuple of (all_valid, modified_files, missing_files)
    """
    if not MANIFEST_PATH.exists():
        return False, [], ["Manifest file not found"]
        
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    stored_checksums = manifest.get("checksums", {})
    all_valid = True
    modified_files = []
    missing_files = []
    
    # Check each stored checksum
    for rel_path, expected_hash in stored_checksums.items():
        full_path = PROJECT_ROOT / rel_path
        
        if not full_path.exists():
            missing_files.append(rel_path)
            all_valid = False
            continue
            
        current_hash = compute_sha256(full_path)
        
        if current_hash != expected_hash:
            modified_files.append(rel_path)
            all_valid = False
            
    # Also check for new files not in manifest
    current_files = set()
    for dir_name in ARTIFACT_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        for artifact in scan_directory(dir_path):
            rel_path = str(artifact.relative_to(PROJECT_ROOT))
            current_files.add(rel_path)
            
    stored_files = set(stored_checksums.keys())
    new_files = current_files - stored_files
    
    if new_files:
        # New files are not necessarily invalid, but worth noting
        pass
        
    return all_valid, modified_files, missing_files

def compute_and_save_manifest() -> Dict[str, str]:
    """
    Scan all artifact directories, compute checksums, and save to manifest.
    
    Returns:
        Dictionary of relative_path -> sha256_hash
    """
    checksums = {}
    
    for dir_name in ARTIFACT_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue
            
        artifacts = scan_directory(dir_path)
        for artifact in artifacts:
            rel_path = str(artifact.relative_to(PROJECT_ROOT))
            checksums[rel_path] = compute_sha256(artifact)
            
    save_checksum_manifest(checksums, {
        "artifact_count": len(checksums),
        "scan_time": datetime.now(timezone.utc).isoformat(),
    })
    
    return checksums

def main() -> int:
    """
    Main entry point for the checksum script.
    
    Usage:
        python code/checksum.py [command]
        
    Commands:
        compute  - Compute checksums for all artifacts and save to manifest
        verify   - Verify artifacts against stored manifest
        status   - Show summary of artifact status
    """
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if command == "compute":
        print("Computing checksums for all artifacts...")
        checksums = compute_and_save_manifest()
        print(f"Computed {len(checksums)} checksums.")
        print(f"Manifest saved to: {MANIFEST_PATH}")
        return 0
        
    elif command == "verify":
        print("Verifying artifact checksums...")
        all_valid, modified, missing = verify_checksums()
        
        if all_valid:
            print("✓ All artifacts verified successfully.")
            return 0
        else:
            print("✗ Verification failed!")
            
            if modified:
                print("\nModified files:")
                for f in modified:
                    print(f"  - {f}")
                    
            if missing:
                print("\nMissing files:")
                for f in missing:
                    print(f"  - {f}")
                    
            return 1
            
    elif command == "status":
        if not MANIFEST_PATH.exists():
            print("No manifest found. Run 'compute' first.")
            return 1
            
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        print(f"Manifest version: {manifest.get('version', 'unknown')}")
        print(f"Created at: {manifest.get('created_at', 'unknown')}")
        print(f"Artifact count: {len(manifest.get('checksums', {}))}")
        
        # Quick verification
        all_valid, modified, missing = verify_checksums()
        if all_valid:
            print("Status: ✓ All artifacts intact")
        else:
            print("Status: ✗ Issues detected")
            if modified:
                print(f"  Modified: {len(modified)}")
            if missing:
                print(f"  Missing: {len(missing)}")
                
        return 0 if all_valid else 1
        
    else:
        print(f"Unknown command: {command}")
        print("Usage: python code/checksum.py [compute|verify|status]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
