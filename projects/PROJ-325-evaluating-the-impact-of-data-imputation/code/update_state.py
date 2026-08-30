import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("state/manifest.yaml")

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_artifacts(base_dir: Path = Path(".")) -> list[Path]:
    """Find all data artifacts in the project."""
    artifacts = []
    for ext in ["*.csv", "*.json", "*.parquet", "*.yaml", "*.yml"]:
        artifacts.extend(base_dir.rglob(ext))
    return [p for p in artifacts if "cache" not in str(p) and "__pycache__" not in str(p)]

def generate_manifest(artifacts: list[Path]) -> Dict[str, Any]:
    """Generate a manifest dictionary from a list of artifacts."""
    manifest = {
        "artifact_hashes": {},
        "status": "pending",
        "last_updated": None
    }
    for path in artifacts:
        try:
            hash_val = compute_file_hash(path)
            manifest["artifact_hashes"][str(path)] = hash_val
        except Exception as e:
            logger.warning(f"Could not compute hash for {path}: {e}")
    return manifest

def update_manifest(
    artifact_path: str,
    hash_value: Optional[str] = None,
    status: Optional[str] = None,
    force: bool = False
):
    """
    Update the manifest.yaml file with a specific artifact's hash and status.
    If hash_value is None, it is computed from the file.
    """
    path = Path(artifact_path)
    
    # Load existing manifest or create new
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {"artifact_hashes": {}, "status": "pending"}

    # Ensure artifact_hashes exists
    if "artifact_hashes" not in manifest:
        manifest["artifact_hashes"] = {}

    # Compute hash if not provided
    if hash_value is None:
        if path.exists():
            hash_value = compute_file_hash(path)
        else:
            if not force:
                logger.warning(f"File not found for hash computation: {path}")
                return

    # Update entry
    manifest["artifact_hashes"][str(path)] = hash_value
    if status:
        manifest["status"] = status
    
    # Ensure state directory exists
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    logger.info(f"Updated manifest for {path} with status {status}")

def main():
    """CLI entry point to regenerate the full manifest."""
    artifacts = find_artifacts()
    manifest = generate_manifest(artifacts)
    
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    logger.info(f"Manifest updated at {MANIFEST_PATH} with {len(manifest['artifact_hashes'])} artifacts.")

if __name__ == "__main__":
    main()