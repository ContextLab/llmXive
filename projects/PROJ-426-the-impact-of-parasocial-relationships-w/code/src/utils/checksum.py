"""
Utility script to compute SHA‑256 checksums for all data artifacts
(raw, processed, results, etc.) and store them in a manifest file.

The manifest is written as a YAML mapping from each file's relative
path (with POSIX separators) to its hex‑digest checksum.

This script is intended to be invoked as part of the pipeline
(e.g. via the quickstart or a CI step) and will create
``data/artifact_manifest.yaml`` under the project root.
"""

import hashlib
from pathlib import Path
from typing import Dict

import yaml

# llmxive toolkit helpers for consistent path handling
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a single file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    hash_sha256 = hashlib.sha256()
    # Read the file in chunks to avoid loading large files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def gather_artifact_checksums(root_data_dir: Path) -> Dict[str, str]:
    """
    Walk through ``root_data_dir`` (the ``data`` folder) and compute a
    checksum for every regular file found.

    The returned dictionary maps each file's **relative POSIX path**
    (relative to the project root) to its checksum.

    Parameters
    ----------
    root_data_dir: Path
        Absolute path to the ``data`` directory.

    Returns
    -------
    Dict[str, str]
        Mapping of relative file paths to SHA‑256 checksums.
    """
    manifest: Dict[str, str] = {}
    for file_path in root_data_dir.rglob("*"):
        if file_path.is_file():
            # Relative path from the project root, using forward slashes
            rel_path = file_path.relative_to(paths.root).as_posix()
            checksum = compute_sha256(file_path)
            manifest[rel_path] = checksum
            log.debug("Checksum computed for %s: %s", rel_path, checksum)
    return manifest


def write_manifest(manifest: Dict[str, str], output_path: Path) -> None:
    """
    Write the checksum manifest to ``output_path`` as YAML.

    Parameters
    ----------
    manifest: Dict[str, str]
        Mapping of relative file paths to checksums.
    output_path: Path
        Destination path for ``artifact_manifest.yaml``.
    """
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)

    log.info("Artifact manifest written to %s (%d entries)", output_path, len(manifest))


def main() -> None:
    """
    Entry point for the checksum utility.

    It computes checksums for every file under the ``data`` directory
    and writes ``data/artifact_manifest.yaml``.
    """
    # Resolve the absolute path to the project's ``data`` folder
    data_dir = paths.data()
    manifest_path = paths.data("artifact_manifest.yaml")

    log.info("Starting checksum generation for all artifacts in %s", data_dir)

    if not data_dir.exists():
        log.error("Data directory does not exist: %s", data_dir)
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    manifest = gather_artifact_checksums(data_dir)
    write_manifest(manifest, manifest_path)

    log.info("Checksum generation completed successfully.")


if __name__ == "__main__":
    # When executed as a script, run the main routine.
    main()
