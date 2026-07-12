import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
HASHES_DIR = STATE_DIR / "hashes"
MANIFEST_PATH = STATE_DIR / "manifest.json"
TARGET_DIRS = ["code", "data"]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_directories() -> None:
    """Ensure state and hashes directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HASHES_DIR.mkdir(parents=True, exist_ok=True)

def get_files_to_hash() -> List[Path]:
    """Get list of all files in code/ and data/ directories."""
    files = []
    for dir_name in TARGET_DIRS:
        target_path = PROJECT_ROOT / dir_name
        if target_path.exists():
            for file_path in target_path.rglob("*"):
                if file_path.is_file():
                    files.append(file_path)
    return files

def generate_manifest() -> Dict[str, Any]:
    """Generate the manifest dictionary with file paths and hashes."""
    ensure_directories()
    files = get_files_to_hash()
    manifest_entries = []

    for file_path in sorted(files):
        relative_path = file_path.relative_to(PROJECT_ROOT)
        file_hash = calculate_sha256(file_path)
        
        # Store individual hash file
        hash_file_path = HASHES_DIR / f"{relative_path}.sha256"
        hash_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(hash_file_path, "w") as f:
            f.write(file_hash)
        
        manifest_entries.append({
            "path": str(relative_path),
            "sha256": file_hash
        })

    return {"files": manifest_entries}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest to state/manifest.json."""
    ensure_directories()
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {MANIFEST_PATH}")

def verify_manifest() -> bool:
    """Verify the current state against the stored manifest."""
    if not MANIFEST_PATH.exists():
        print("Manifest not found. Run generate_manifest first.")
        return False

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    all_valid = True
    for entry in manifest["files"]:
        file_path = PROJECT_ROOT / entry["path"]
        if not file_path.exists():
            print(f"Missing file: {entry['path']}")
            all_valid = False
            continue
        
        current_hash = calculate_sha256(file_path)
        if current_hash != entry["sha256"]:
            print(f"Hash mismatch for {entry['path']}: expected {entry['sha256']}, got {current_hash}")
            all_valid = False

    if all_valid:
        print("All files verified successfully.")
    return all_valid

def main() -> None:
    """Main entry point for manifest generation."""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_manifest()
    else:
        manifest = generate_manifest()
        save_manifest(manifest)
        print(f"Generated manifest with {len(manifest['files'])} files.")

if __name__ == "__main__":
    main()