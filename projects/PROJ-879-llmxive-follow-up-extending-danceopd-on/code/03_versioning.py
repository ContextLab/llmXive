#!/usr/bin/env python
"""
Versioning utility for the llmXive follow‑up project.

This script computes the SHA‑256 hash of a given artifact and records the
hash in ``state/artifact_hashes.yaml``. The YAML file maps the string
representation of the artifact path to its hash, enabling reproducible
verification of generated data, models, and other pipeline outputs.

Usage
-----
python code/03_versioning.py --artifact <path-to-artifact>

The script will:
  1. Verify that the artifact exists.
  2. Compute its SHA‑256 hash (stream‑reading to handle large files).
  3. Load (or create) ``state/artifact_hashes.yaml``.
  4. Update the mapping with the new hash.
  5. Write the updated YAML back to disk.

The script exits with status 0 on success and 1 on failure.
"""
import argparse
import hashlib
import sys
from pathlib import Path
import logging
import yaml

# Project utilities
from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file.

    The file is read in 4 KiB chunks to avoid loading large files
    entirely into memory.

    Parameters
    ----------
    file_path: Path
        Path to the file whose hash should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256_hash = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise
    return sha256_hash.hexdigest()


def load_hashes_yaml(yaml_path: Path) -> dict:
    """
    Load the existing artifact hash mapping from a YAML file.

    If the file does not exist, an empty dictionary is returned.

    Parameters
    ----------
    yaml_path: Path
        Path to the YAML file.

    Returns
    -------
    dict
        Mapping of artifact string paths to SHA‑256 hashes.
    """
    if not yaml_path.exists():
        logger.info(f"Hash manifest does not exist; creating new one at {yaml_path}")
        return {}
    try:
        with yaml_path.open("r") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                logger.warning(
                    f"Unexpected content in {yaml_path}; resetting to empty dict."
                )
                return {}
            return data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {yaml_path}: {e}")
        raise


def save_hashes_yaml(yaml_path: Path, data: dict) -> None:
    """
    Write the artifact‑hash mapping to a YAML file.

    Parameters
    ----------
    yaml_path: Path
        Destination YAML file.
    data: dict
        Mapping to write.
    """
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with yaml_path.open("w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as e:
        logger.error(f"Failed to write YAML file {yaml_path}: {e}")
        raise


def version_artifact(config, artifact_path: Path) -> None:
    """
    Compute the hash of ``artifact_path`` and update the manifest.

    Parameters
    ----------
    config: Config
        Project configuration object (from ``utils.config``).
    artifact_path: Path
        Path to the artifact to be versioned.
    """
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        sys.exit(1)

    # Compute hash
    file_hash = calculate_sha256(artifact_path)
    logger.info(f"Computed SHA‑256 for {artifact_path}: {file_hash}")

    # Determine manifest location
    project_root = Path(config.get_path("PROJECT_ROOT"))
    manifest_path = project_root / "state" / "artifact_hashes.yaml"

    # Load existing mappings, update, and write back
    hashes = load_hashes_yaml(manifest_path)
    # Store the artifact path relative to the project root for readability
    rel_path = str(artifact_path.relative_to(project_root))
    hashes[rel_path] = file_hash
    save_hashes_yaml(manifest_path, hashes)

    logger.info(f"Updated hash manifest at {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Version an artifact by computing its SHA‑256 hash and storing it in state/artifact_hashes.yaml"
    )
    parser.add_argument(
        "--artifact",
        type=str,
        required=True,
        help="Path to the artifact file to version (absolute or relative to project root).",
    )
    args = parser.parse_args()

    config = get_config()
    artifact_path = Path(args.artifact)

    # If a relative path is provided, resolve it against the project root
    if not artifact_path.is_absolute():
        project_root = Path(config.get_path("PROJECT_ROOT"))
        artifact_path = project_root / artifact_path

    version_artifact(config, artifact_path)


if __name__ == "__main__":
    main()