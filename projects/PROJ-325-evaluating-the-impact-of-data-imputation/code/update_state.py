import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("state/manifest.yaml")

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_artifacts(base_dir: str = "data") -> Dict[str, str]:
    """Find all generated artifacts and compute their hashes."""
    artifacts = {}
    base = Path(base_dir)
    if not base.exists():
        return artifacts
    
    for file_path in base.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(Path(".")))
            artifacts[relative_path] = compute_file_hash(str(file_path))
    return artifacts

def load_manifest() -> Dict[str, Any]:
    """Load existing manifest or return empty dict."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def update_manifest(artifacts: Dict[str, str], manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Update manifest with new artifact hashes."""
    manifest['artifact_hashes'] = artifacts
    manifest['updated_at'] = str(Path().cwd().resolve()) # Simple timestamp placeholder
    return manifest

def generate_manifest(output_path: str = "state/manifest.yaml"):
    """Generate a new manifest file."""
    artifacts = find_artifacts()
    manifest = {'artifact_hashes': artifacts}
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    logger.info(f"Generated manifest at {output_path}")

def main():
    """Main entry point to update the manifest."""
    ensure_dir = Path(MANIFEST_PATH).parent
    ensure_dir.mkdir(parents=True, exist_ok=True)
    
    artifacts = find_artifacts()
    manifest = load_manifest()
    updated_manifest = update_manifest(artifacts, manifest)
    
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(updated_manifest, f, default_flow_style=False)
    
    logger.info(f"Manifest updated with {len(artifacts)} artifacts.")

if __name__ == '__main__':
    main()
