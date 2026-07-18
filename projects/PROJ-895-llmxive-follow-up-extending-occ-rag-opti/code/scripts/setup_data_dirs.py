import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

def ensure_dir(path: str) -> Path:
    """Ensure the directory for a given path exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def init_checksums(checksum_file_path: str) -> Dict[str, Any]:
    """Initialize or load the checksums.json file."""
    if os.path.exists(checksum_file_path):
        with open(checksum_file_path, "r") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "artifacts": {}
    }

def register_artifact(
    checksums: Dict[str, Any],
    artifact_path: str,
    artifact_name: str,
    description: Optional[str] = None
) -> None:
    """Register an artifact in the checksums dictionary."""
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    checksum = compute_sha256(artifact_path)
    size_bytes = os.path.getsize(artifact_path)
    
    checksums["artifacts"][artifact_name] = {
        "path": artifact_path,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "description": description or "No description provided",
        "version": "1.0"
    }

def main():
    """Main entry point to setup data directories and initialize checksums."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    data_raw_dir = project_root / "data" / "raw"
    checksums_file = project_root / "data" / "checksums.json"
    
    # Ensure directories exist
    ensure_dir(str(data_raw_dir))
    
    # Initialize checksums
    checksums = init_checksums(str(checksums_file))
    
    # Register the raw data directory placeholder if needed (optional)
    # Note: T004 creates the actual corpus file, so we don't register it here yet.
    # This script ensures the structure is ready for T004.
    
    # Save updated checksums
    with open(checksums_file, "w") as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Data directories created: {data_raw_dir}")
    print(f"Checksums file initialized: {checksums_file}")

if __name__ == "__main__":
    main()
