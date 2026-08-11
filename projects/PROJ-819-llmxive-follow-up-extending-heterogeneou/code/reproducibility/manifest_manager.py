import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def ensure_directories(base_path: Path) -> None:
    """Ensure required directories exist."""
    (base_path / "hashes").mkdir(parents=True, exist_ok=True)

def get_files_to_hash(root_path: Path, target_dirs: List[str]) -> List[Path]:
    """Recursively get all files in target directories."""
    files = []
    for dir_name in target_dirs:
        target_dir = root_path / dir_name
        if target_dir.exists():
            for file_path in target_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    files.append(file_path)
    return files

def generate_manifest(files: List[Path], base_path: Path) -> Dict[str, Any]:
    """Generate manifest dictionary with file paths and hashes."""
    files_data = []
    for file_path in files:
        relative_path = file_path.relative_to(base_path)
        file_hash = calculate_sha256(file_path)
        files_data.append({
            "path": str(relative_path),
            "sha256": file_hash
        })
    return {"files": files_data}

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save manifest to JSON file."""
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

def verify_manifest(manifest_path: Path, base_path: Path) -> bool:
    """Verify manifest against current file system state."""
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    for file_entry in manifest["files"]:
        file_path = base_path / file_entry["path"]
        if not file_path.exists():
            return False
        current_hash = calculate_sha256(file_path)
        if current_hash != file_entry["sha256"]:
            return False
    return True

def main():
    """Main entry point for manifest generation."""
    base_path = Path(__file__).parent.parent.parent  # Go up to project root
    state_dir = base_path / "state"
    ensure_directories(state_dir)
    
    # Hash files in 'data' and 'code' directories
    target_dirs = ["data", "code"]
    files = get_files_to_hash(base_path, target_dirs)
    
    manifest = generate_manifest(files, base_path)
    manifest_path = state_dir / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    print(f"Manifest generated at {manifest_path}")
    print(f"Total files hashed: {len(manifest['files'])}")
    
    return manifest_path

if __name__ == "__main__":
    main()
