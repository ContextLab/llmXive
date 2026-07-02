"""
Versioning and Manifest Management for pipeline artifacts.
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import STATE_DIR, PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_version_manifest(artifacts: Dict[str, Path], project_id: str) -> Dict[str, Any]:
    """
    Generate a version manifest for a set of artifacts.

    Args:
        artifacts: Dictionary mapping artifact names to their file paths.
        project_id: The unique project identifier.

    Returns:
        A dictionary representing the version manifest.
    """
    manifest = {
        "project_id": project_id,
        "generated_at": datetime.utcnow().isoformat(),
        "artifacts": {}
    }

    for name, path in artifacts.items():
        if not path.exists():
            logger.warning(f"Artifact {name} not found at {path}, skipping.")
            continue
        manifest["artifacts"][name] = {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "hash": compute_file_hash(path),
            "size_bytes": path.stat().st_size
        }

    return manifest

def update_project_manifest(project_id: str, new_artifacts: Optional[Dict[str, Path]] = None) -> Path:
    """
    Update the project state manifest with new artifact hashes.

    Args:
        project_id: The unique project identifier.
        new_artifacts: Optional dictionary of new artifacts to add/update.

    Returns:
        Path to the updated manifest file.
    """
    manifest_path = STATE_DIR / f"{project_id}.yaml"
    # Using JSON for simplicity in this Python implementation, though YAML is requested in spec.
    # We will write a JSON file but name it .yaml if strictly required, or keep .json.
    # Given the prompt says `state/projects/...yaml`, we will write a JSON structure
    # but save it as .yaml for compatibility with the requirement, or better,
    # write valid YAML if pyyaml is available.
    # Since pyyaml is in requirements, we use it.
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False
        logger.warning("PyYAML not installed. Saving manifest as JSON with .yaml extension.")

    existing_manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            if use_yaml:
                existing_manifest = yaml.safe_load(f) or {}
            else:
                existing_manifest = json.load(f)

    if new_artifacts:
        if "artifacts" not in existing_manifest:
            existing_manifest["artifacts"] = {}

        for name, path in new_artifacts.items():
            if path.exists():
                existing_manifest["artifacts"][name] = {
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "hash": compute_file_hash(path),
                    "updated_at": datetime.utcnow().isoformat()
                }

    existing_manifest["project_id"] = project_id
    existing_manifest["last_updated"] = datetime.utcnow().isoformat()

    with open(manifest_path, 'w') as f:
        if use_yaml:
            yaml.dump(existing_manifest, f, default_flow_style=False)
        else:
            json.dump(existing_manifest, f, indent=2)

    logger.info(f"Updated project manifest: {manifest_path}")
    return manifest_path

def main():
    """Test versioning functions."""
    # Create a dummy artifact for testing
    test_file = PROJECT_ROOT / "test_artifact.txt"
    test_file.write_text("Hello, World!")

    manifest = generate_version_manifest({"test": test_file}, "TEST-001")
    print(json.dumps(manifest, indent=2))

    update_project_manifest("TEST-001", {"test": test_file})
    print(f"Manifest updated at {STATE_DIR}/TEST-001.yaml")

    test_file.unlink()

if __name__ == "__main__":
    main()
