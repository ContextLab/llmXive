"""
code/reproducibility/manifest_manager.py

Implements the continuous hook for T010: Manifest Manager.
Computes SHA-256 hashes for all files in code/ and data/ and saves to state/manifest.json.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_directories(base_path: Path) -> None:
    """Ensure required directories exist."""
    (base_path / "state").mkdir(parents=True, exist_ok=True)
    (base_path / "state" / "hashes").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "derived").mkdir(parents=True, exist_ok=True)

def get_files_to_hash(root_path: Path) -> List[Path]:
    """Recursively get all files in code/ and data/ directories."""
    files = []
    target_dirs = ["code", "data"]
    
    for target_dir in target_dirs:
        dir_path = root_path / target_dir
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    files.append(file_path)
    
    return files

def generate_manifest(root_path: Path) -> Dict[str, Any]:
    """Generate the manifest dictionary with file hashes."""
    files = get_files_to_hash(root_path)
    manifest_files = []
    
    for file_path in files:
        rel_path = str(file_path.relative_to(root_path))
        file_hash = calculate_sha256(str(file_path))
        manifest_files.append({
            "path": rel_path,
            "sha256": file_hash
        })
    
    return {
        "files": manifest_files
    }

def save_manifest(root_path: Path, manifest: Dict[str, Any]) -> None:
    """Save the manifest to state/manifest.json."""
    manifest_path = root_path / "state" / "manifest.json"
    ensure_directories(root_path)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest saved to {manifest_path}")

def verify_manifest(root_path: Path) -> bool:
    """Verify the manifest against current file hashes."""
    manifest_path = root_path / "state" / "manifest.json"
    
    if not manifest_path.exists():
        print("Manifest file not found.")
        return False
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    current_manifest = generate_manifest(root_path)
    
    # Compare files
    current_files = {f["path"]: f["sha256"] for f in current_manifest["files"]}
    stored_files = {f["path"]: f["sha256"] for f in manifest["files"]}
    
    if set(current_files.keys()) != set(stored_files.keys()):
        print("File list mismatch.")
        return False
    
    for path, stored_hash in stored_files.items():
        if current_files.get(path) != stored_hash:
            print(f"Hash mismatch for {path}")
            return False
    
    print("Manifest verification successful.")
    return True

def main():
    """Main entry point to generate and save manifest."""
    root_path = Path(__file__).resolve().parent.parent
    manifest = generate_manifest(root_path)
    save_manifest(root_path, manifest)

if __name__ == "__main__":
    main()
