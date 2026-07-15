import os
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "data/processed",
    "results/benchmarks",
    "results/figures",
    "results/stats",
    "logs",
]

CHECKSUM_FILE = "results/checksums.json"

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def setup_directories(base_path: str = ".") -> List[str]:
    """Create required directory structure if it doesn't exist."""
    base = Path(base_path)
    created = []
    for dir_name in REQUIRED_DIRS:
        full_path = base / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        elif not full_path.is_dir():
            raise RuntimeError(f"Path {full_path} exists but is not a directory")
    return created

def generate_checksums(base_path: str = ".", files: List[str] = None) -> Dict[str, str]:
    """Generate checksums for all files in results/benchmarks and data/processed."""
    base = Path(base_path)
    checksums = {}
    
    # Scan specific directories
    target_dirs = [base / "results/benchmarks", base / "data/processed"]
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(base))
                checksums[rel_path] = compute_file_checksum(str(file_path))
    
    # Save checksums
    checksum_file = base / CHECKSUM_FILE
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)
    
    return checksums

def verify_directories(base_path: str = ".") -> Tuple[bool, List[str]]:
    """Verify that all required directories exist and checksums match if file exists."""
    base = Path(base_path)
    missing = []
    issues = []
    
    # Check directories
    for dir_name in REQUIRED_DIRS:
        full_path = base / dir_name
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_name)
    
    # Verify checksums if file exists
    checksum_file = base / CHECKSUM_FILE
    if checksum_file.exists():
        with open(checksum_file, "r") as f:
            stored_checksums = json.load(f)
        
        for rel_path, stored_hash in stored_checksums.items():
            full_path = base / rel_path
            if not full_path.exists():
                issues.append(f"Missing file: {rel_path}")
            else:
                current_hash = compute_file_checksum(str(full_path))
                if current_hash != stored_hash:
                    issues.append(f"Checksum mismatch: {rel_path}")
    else:
        # No checksum file yet, just check directories
        pass
    
    return len(missing) == 0 and len(issues) == 0, missing + issues

def main():
    """Main entry point for directory setup and verification."""
    base_path = Path(__file__).parent.parent
    
    print(f"Setting up directories in {base_path}...")
    created = setup_directories(str(base_path))
    if created:
        print(f"Created directories: {created}")
    else:
        print("All required directories already exist.")
    
    print("Generating checksums...")
    checksums = generate_checksums(str(base_path))
    print(f"Checksums saved to {base_path / CHECKSUM_FILE}")
    print(f"Total files checksummed: {len(checksums)}")
    
    print("Verifying structure...")
    is_valid, issues = verify_directories(str(base_path))
    if is_valid:
        print("✓ Directory structure verified successfully.")
        return 0
    else:
        print("✗ Verification failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

if __name__ == "__main__":
    sys.exit(main())