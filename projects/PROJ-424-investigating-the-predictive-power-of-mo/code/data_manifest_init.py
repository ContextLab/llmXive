"""
Initialize the data manifest with checksums.

This script verifies the existence of data files and generates a manifest
containing their SHA256 checksums for integrity verification.
"""
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW_DIR / "manifest.json"
NIST_REFS_PATH = DATA_RAW_DIR / "nist_refs.json"

def compute_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_gitkeep(directory: Path):
    """Ensure a .gitkeep file exists in the directory."""
    gitkeep = directory / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

def init_manifest() -> Path:
    """Generate the manifest.json with checksums for all data files."""
    if not DATA_RAW_DIR.exists():
        raise FileNotFoundError(f"Data directory {DATA_RAW_DIR} does not exist.")
    
    ensure_gitkeep(DATA_RAW_DIR)
    
    files_info = {}
    for file_path in DATA_RAW_DIR.iterdir():
        if file_path.is_file() and file_path.name != ".gitkeep":
            checksum = compute_file_hash(file_path)
            files_info[file_path.name] = {
                "path": str(file_path.relative_to(PROJECT_ROOT)),
                "sha256": checksum,
                "size_bytes": file_path.stat().st_size
            }
    
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "files": files_info
    }
    
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Generated: {MANIFEST_PATH}")
    print(f"Files indexed: {len(files_info)}")
    for name, info in files_info.items():
        print(f"  - {name}: {info['sha256'][:16]}...")
    
    return MANIFEST_PATH

def main():
    """Main entry point."""
    try:
        init_manifest()
        print("SUCCESS: Manifest initialized.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
