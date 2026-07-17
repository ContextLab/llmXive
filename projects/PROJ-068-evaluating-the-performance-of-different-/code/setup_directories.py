import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_PROJECT_NAME = "PROJ-068-evaluating-the-performance-of-different-"

REQUIRED_SUBDIRS = [
    "code",
    "tests",
    "data",
    "results",
    "data/processed",
    "results/benchmarks",
    "results/figures",
]

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def setup_directories(base_path: Path, subdirs: List[str]) -> List[Path]:
    """Create all required subdirectories under base_path."""
    created_paths = []
    for subdir in subdirs:
        full_path = base_path / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)
        print(f"Created directory: {full_path.relative_to(base_path)}")
    return created_paths

def generate_checksums(base_path: Path, checksum_file: Path) -> None:
    """Generate a JSON file containing checksums for all created directories."""
    checksums = {}
    # We checksum the directory markers or just record existence
    # Since directories don't have content to hash in the same way,
    # we record the timestamp and existence, or hash a .gitkeep if present.
    # For this task, we record the path and a placeholder 'created' status
    # or hash the path string itself to ensure determinism.
    
    # Let's hash the relative path string to have a stable "checksum" for the structure
    for subdir in REQUIRED_SUBDIRS:
        full_path = base_path / subdir
        if full_path.exists():
            content_to_hash = f"{full_path.relative_to(base_path)}\n"
            sha = hashlib.sha256(content_to_hash.encode()).hexdigest()
            checksums[str(full_path.relative_to(base_path))] = {
                "checksum": sha,
                "exists": True,
                "type": "directory"
            }
    
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)
    print(f"Checksums written to: {checksum_file}")

def verify_directories(base_path: Path, checksum_file: Path) -> bool:
    """Verify directories exist against the checksum manifest."""
    if not checksum_file.exists():
        print("Checksum file not found. Cannot verify.")
        return False

    with open(checksum_file, "r") as f:
        checksums = json.load(f)

    all_ok = True
    for rel_path, data in checksums.items():
        full_path = base_path / rel_path
        if not full_path.exists():
            print(f"[FAIL] Missing: {rel_path}")
            all_ok = False
        else:
            print(f"[OK] {rel_path}")
    
    return all_ok

def main():
    """Main entry point to setup and verify project structure."""
    target_root = PROJECT_ROOT / TARGET_PROJECT_NAME
    
    print(f"Setting up project structure at: {target_root}")
    
    # Create the root project directory if it doesn't exist
    target_root.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    setup_directories(target_root, REQUIRED_SUBDIRS)
    
    # Generate checksums for verification
    checksum_file = target_root / ".project_structure_checksum.json"
    generate_checksums(target_root, checksum_file)
    
    # Verify
    if verify_directories(target_root, checksum_file):
        print("\n[SUCCESS] Project structure verified.")
        sys.exit(0)
    else:
        print("\n[FAIL] Project structure verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()