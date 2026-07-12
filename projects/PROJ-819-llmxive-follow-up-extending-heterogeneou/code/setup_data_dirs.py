import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def ensure_directories(base_path: Path) -> None:
    """Ensure the required directory structure exists."""
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "state" / "hashes",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_data_files(base_path: Path) -> List[Path]:
    """Get all files in data directories for checksumming."""
    files = []
    data_dirs = [base_path / "data" / "raw", base_path / "data" / "derived"]
    for data_dir in data_dirs:
        if data_dir.exists():
          files.extend(data_dir.rglob("*"))
    return [f for f in files if f.is_file()]

def generate_checksums(base_path: Path) -> Dict[str, str]:
    """Generate checksums for all files in data directories."""
    checksums = {}
    files = get_data_files(base_path)
    for file_path in files:
        rel_path = file_path.relative_to(base_path)
        checksum = calculate_sha256(file_path)
        if checksum:
            checksums[str(rel_path)] = checksum
    return checksums

def save_checksums(base_path: Path, checksums: Dict[str, str]) -> None:
    """Save checksums to state/hashes/checksums.json."""
    checksum_file = base_path / "state" / "hashes" / "checksums.json"
    with open(checksum_file, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

def main() -> None:
    """Main entry point for T011: Create directories and checksumming hooks."""
    project_root = Path(__file__).resolve().parent.parent
    
    # 1. Create directory structure
    ensure_directories(project_root)
    
    # 2. Generate initial checksums (empty or existing files)
    checksums = generate_checksums(project_root)
    
    # 3. Save checksums to state/hashes/checksums.json
    save_checksums(project_root, checksums)
    
    print(f"Directories created under {project_root / 'data'}")
    print(f"Checksums saved to {project_root / 'state' / 'hashes' / 'checksums.json'}")
    print(f"Total files checksummed: {len(checksums)}")

if __name__ == "__main__":
    main()