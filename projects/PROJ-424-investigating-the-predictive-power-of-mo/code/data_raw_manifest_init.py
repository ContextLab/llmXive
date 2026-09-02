"""
Initializes the data manifest for the NIST references file.
This script computes the checksum for nist_refs.json and writes it to the manifest.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Project root relative to this file (assuming code/data_raw_manifest_init.py)
# We need to go up to project root, then into data/raw
# However, to be safe and consistent with T001 structure, we assume this runs from project root
# or we use absolute paths based on the file location.

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # Determine paths relative to the project root
    # Assuming this script is run from the project root or we adjust paths accordingly.
    # The task specifies: code/data/raw/nist_refs.json
    # And manifest at: data/raw/manifest.json (per T004)
    
    # Let's assume the working directory is the project root.
    project_root = Path.cwd()
    nist_file = project_root / "code" / "data" / "raw" / "nist_refs.json"
    manifest_file = project_root / "data" / "raw" / "manifest.json"
    
    if not nist_file.exists():
        raise FileNotFoundError(f"NIST references file not found at {nist_file}. "
                                "Run the generation script or ensure T006b artifacts are present.")
    
    # Compute hash
    file_hash = compute_file_hash(nist_file)
    
    # Load or initialize manifest
    manifest_data = {
        "files": {}
    }
    
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            manifest_data = json.load(f)
    
    # Update entry for nist_refs.json
    manifest_data["files"]["nist_refs.json"] = {
        "path": str(nist_file.relative_to(project_root)),
        "sha256": file_hash,
        "size_bytes": nist_file.stat().st_size,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "description": "Curated experimental diffusion coefficients for water, ethanol, acetone at 298K."
    }
    
    # Write manifest
    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"Manifest updated successfully at {manifest_file}")
    print(f"File: nist_refs.json")
    print(f"SHA-256: {file_hash}")
    print(f"Size: {manifest_data['files']['nist_refs.json']['size_bytes']} bytes")

if __name__ == "__main__":
    main()
