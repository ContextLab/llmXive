import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_artifacts(base_dir: str = "data") -> list:
    """Find all files in the data directory."""
    artifacts = []
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.warning(f"Directory {base_dir} does not exist.")
        return artifacts
    
    for path in base_path.rglob('*'):
        if path.is_file():
            artifacts.append(str(path))
    return artifacts

def load_manifest(manifest_path: str = "state/manifest.yaml") -> Dict[str, Any]:
    """Load the manifest file."""
    path = Path(manifest_path)
    if not path.exists():
        logger.info(f"Manifest not found at {manifest_path}, creating new one.")
        return {"artifact_hashes": {}}
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {"artifact_hashes": {}}
    except Exception as e:
        logger.error(f"Error loading manifest: {e}")
        return {"artifact_hashes": {}}

def update_manifest(manifest: Dict[str, Any], file_path: str, hash_val: str) -> Dict[str, Any]:
    """Update manifest with a new file hash."""
    if "artifact_hashes" not in manifest:
        manifest["artifact_hashes"] = {}
    manifest["artifact_hashes"][file_path] = hash_val
    return manifest

def generate_manifest(output_path: str = "state/manifest.yaml") -> Dict[str, Any]:
    """Scan data directory and generate/update manifest."""
    ensure_directories(output_path)
    manifest = load_manifest(output_path)
    artifacts = find_artifacts("data")
    
    for artifact in artifacts:
        try:
            h = compute_file_hash(artifact)
            manifest = update_manifest(manifest, artifact, h)
        except Exception as e:
            logger.error(f"Skipping {artifact}: {e}")
    
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    logger.info(f"Manifest updated at {output_path}")
    return manifest

def update_manifest_with_checksum(file_path: str, manifest_path: str = "state/manifest.yaml") -> str:
    """Compute checksum for a file and update manifest."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    h = compute_file_hash(file_path)
    manifest = load_manifest(manifest_path)
    manifest = update_manifest(manifest, file_path, h)
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    logger.info(f"Updated manifest with checksum for {file_path}")
    return h

def ensure_directories(path: str) -> Path:
    """Ensure directory for path exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update state manifest with artifact checksums.")
    parser.add_argument('--file', type=str, help="Specific file to add to manifest.")
    parser.add_argument('--scan', action='store_true', help="Scan entire data directory.")
    parser.add_argument('--output', type=str, default="state/manifest.yaml", help="Manifest output path.")
    
    args = parser.parse_args()
    
    if args.file:
        update_manifest_with_checksum(args.file, args.output)
    elif args.scan:
        generate_manifest(args.output)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()