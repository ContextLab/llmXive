import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_directories(base_path: Path) -> None:
    """Ensure the state/hashes directory exists."""
    hashes_dir = base_path / "state" / "hashes"
    hashes_dir.mkdir(parents=True, exist_ok=True)

def get_files_to_hash(root_path: Path, directories: List[str]) -> List[Path]:
    """Get all files in specified directories under root_path."""
    files = []
    for dir_name in directories:
        dir_path = root_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and file_path.suffix != ".pyc":
                    files.append(file_path)
    return files

def generate_manifest(files: List[Path], base_path: Path) -> Dict[str, Any]:
    """Generate a manifest dictionary with file paths and SHA-256 hashes."""
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
    """Save the manifest to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def verify_manifest(manifest_path: Path, base_path: Path) -> bool:
    """Verify the manifest against current file hashes."""
    if not manifest_path.exists():
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for file_entry in manifest.get("files", []):
        file_path = base_path / file_entry["path"]
        if not file_path.exists():
            return False

        current_hash = calculate_sha256(file_path)
        if current_hash != file_entry["sha256"]:
            return False

    return True

def main() -> None:
    """Main function to generate and save the manifest."""
    base_path = Path(__file__).resolve().parent.parent.parent
    data_dirs = ["data", "code"]
    
    ensure_directories(base_path)
    files = get_files_to_hash(base_path, data_dirs)
    manifest = generate_manifest(files, base_path)
    
    manifest_path = base_path / "state" / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    print(f"Manifest generated and saved to {manifest_path}")
    print(f"Total files hashed: {len(files)}")

if __name__ == "__main__":
    main()
