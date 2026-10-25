"""
Checksum manifest generator for the project.

This script walks the entire ``data/`` directory, computes a SHA‑256 hash
for each file (excluding the manifest itself), and writes a JSON manifest
to ``data/checksums.json``. The manifest maps each file's path – relative
to the project root – to its hexadecimal digest.

The module also exposes a ``compute_checksums`` function that can be
imported by tests or other scripts.
"""

import hashlib
import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _iter_data_files(root: Path, manifest_path: Path):
    """
    Yield all regular files under ``root`` excluding ``manifest_path``.
    The yielded paths are absolute ``Path`` objects.
    """
    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.resolve() != manifest_path.resolve():
            yield file_path

def compute_checksums(
    output_path: Path = None,
    data_root: Path = None,
) -> Path:
    """
    Compute SHA‑256 checksums for every file under ``data/`` and write a
    manifest JSON.

    Args:
        output_path: Destination for the manifest. If ``None`` the default
            ``data/checksums.json`` (via ``paths.data``) is used.
        data_root: Root directory to scan. If ``None`` the default data
            directory (``paths.data()``) is used.

    Returns:
        The absolute path to the written manifest file.
    """
    if output_path is None:
        output_path = paths.data("checksums.json")
    if data_root is None:
        data_root = paths.data()

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {}
    for file_path in _iter_data_files(data_root, output_path):
        # Compute SHA‑256
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        checksum = hasher.hexdigest()
        # Store path relative to the project root (POSIX style)
        rel_path = file_path.relative_to(Path.cwd()).as_posix()
        manifest[rel_path] = checksum
        log.debug("Checksum computed: %s -> %s", rel_path, checksum)

    # Write manifest with stable ordering
    with output_path.open("w", encoding="utf-8") as out_f:
        json.dump(manifest, out_f, indent=2, sort_keys=True)

    log.info("Checksum manifest written to %s (%d entries)", output_path, len(manifest))
    return output_path

def main():
    """
    CLI entry point. When the module is executed as a script it simply
    runs ``compute_checksums()`` with the default locations.
    """
    compute_checksums()

if __name__ == "__main__":
    main()
