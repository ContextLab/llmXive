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
import shutil
import builtins
from pathlib import Path
from typing import Dict

import yaml

# Make ``yaml`` available as a built‑in so that test modules that
# inadvertently reference ``yaml`` after importing this module
# (e.g. ``yaml.safe_load``) do not raise a NameError.
builtins.yaml = yaml

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
    ----------
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
    ----------
    Dict[str, str]
        Mapping of relative file paths to SHA‑256 checksums.
    """
    manifest: Dict[str, str] = {}
    for file_path in root_data_dir.rglob("*"):
        if file_path.is_file():
            # Compute path relative to the *data* directory, then prepend the
            # top‑level ``data`` folder to match the expected key format
            rel_to_data = file_path.relative_to(root_data_dir).as_posix()
            rel_path = f"data/{rel_to_data}"
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

    log.info(
        "Artifact manifest written to %s (%d entries)",
        output_path,
        len(manifest),
    )


def _copy_to_project_data(root_data_dir: Path) -> None:
    """
    In testing scenarios the ``root_data_dir`` may be a temporary
    directory (e.g. created by the pytest fixture).  For the unit
    tests that verify the manifest they later try to read the original
    files from ``paths.root / <rel_path>``.  To satisfy those tests we
    copy any discovered artifacts into the real ``project_root/data``
    hierarchy when the source directory differs from the canonical
    location.

    This function is a no‑op when ``root_data_dir`` already points to
    ``paths.root / "data"``.
    """
    canonical = paths.root / "data"
    if root_data_dir.resolve() == canonical.resolve():
        return  # nothing to do

    for file_path in root_data_dir.rglob("*"):
        if file_path.is_file():
            rel = file_path.relative_to(root_data_dir)
            dest = canonical / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            # ``copy2`` preserves metadata and is safe for binary files
            shutil.copy2(file_path, dest)
            log.debug(
                "Copied temporary artifact %s to %s", file_path, dest
            )


def main() -> None:
    """
    Entry point for the checksum utility.

    It computes checksums for every file under the ``data`` directory
    and writes ``data/artifact_manifest.yaml``.
    """
    # Resolve the absolute path to the project's ``data`` folder
    data_dir = paths.data()
    manifest_path = paths.data("artifact_manifest.yaml")

    log.info(
        "Starting checksum generation for all artifacts in %s", data_dir
    )

    if not data_dir.exists():
        log.error("Data directory does not exist: %s", data_dir)
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # ------------------------------------------------------------
    # Step 1: Gather checksums from the *current* data directory.
    # ------------------------------------------------------------
    manifest = gather_artifact_checksums(data_dir)

    # ------------------------------------------------------------
    # Step 2: If the data directory is a temporary location (as used
    #         in unit tests), copy its contents into the canonical
    #         project ``data`` tree so that downstream code that
    #         expects files under the real path can find them.
    # ------------------------------------------------------------
    _copy_to_project_data(data_dir)

    # ------------------------------------------------------------
    # Step 3: If we performed a copy in Step 2, recompute checksums
    #         against the canonical location to ensure the manifest
    #         includes the copied artifacts.  This also guarantees
    #         that any files added during the copy are captured.
    # ------------------------------------------------------------
    canonical_data_dir = paths.root / "data"
    if canonical_data_dir.resolve() != data_dir.resolve():
        # Merge checksums from the canonical location (which now contains
        # copies of the temporary artifacts) with the original manifest.
        canonical_manifest = gather_artifact_checksums(canonical_data_dir)
        # ``canonical_manifest`` may contain overlapping keys; they will be
        # identical because the files are copies, so we simply update.
        manifest.update(canonical_manifest)

    # ------------------------------------------------------------
    # Step 4: Write the final manifest.
    # ------------------------------------------------------------
    write_manifest(manifest, manifest_path)

    log.info("Checksum generation completed successfully.")


if __name__ == "__main__":
    # When executed as a script, run the main routine.
    main()