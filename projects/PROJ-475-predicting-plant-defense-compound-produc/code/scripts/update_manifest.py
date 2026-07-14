"""
Script to update the project manifest (data/manifest.yaml) with correct SHA-256
checksums for all generated artifacts and ensure that every artifact present in
the repository is listed.

The script follows the public API defined in `code/scripts/update_manifest.py`:
- `should_include_file`
- `get_all_artifacts`
- `get_artifact_metadata`
- `update_manifest`
- `main`

It is idempotent: running it multiple times will only refresh the checksum
values and add missing entries without duplicating existing ones.
"""

import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

from utils.io import compute_checksum

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def should_include_file(file_path: Path) -> bool:
    """
    Determine whether a file should be part of the manifest.

    We include files that belong to one of the top‑level artifact
    directories used by the pipeline: ``data/``, ``models/``, ``results/``,
    and ``state/``. Hidden files and the manifest itself are excluded.

    Parameters
    ----------
    file_path: Path
        Path to the file relative to the repository root.

    Returns
    -------
    bool
        True if the file should be recorded in the manifest.
    """
    # Exclude the manifest itself to avoid circular updates
    if file_path == Path("data/manifest.yaml"):
        return False

    # Only regular files (skip directories)
    if not file_path.is_file():
        return False

    # Include only files under the recognised top‑level directories
    top_dirs = ("data", "models", "results", "state")
    return file_path.parts[0] in top_dirs

def get_all_artifacts(repo_root: Path = Path(".")) -> list[Path]:
    """
    Walk the repository and collect all files that should be listed in the
    manifest.

    Parameters
    ----------
    repo_root: Path, optional
        Root directory of the repository (default is current working directory).

    Returns
    -------
    list[Path]
        List of absolute ``Path`` objects for each artifact file.
    """
    artifacts = []
    for root, _, files in os.walk(repo_root):
        for name in files:
            file_path = Path(root) / name
            # Normalise to a relative path from the repository root
            rel_path = file_path.relative_to(repo_root)
            if should_include_file(rel_path):
                artifacts.append(rel_path)
    return artifacts

def infer_artifact_type(file_path: Path) -> str:
    """
    Infer the ``type`` field for a manifest entry based on its top‑level
    directory.

    Parameters
    ----------
    file_path: Path
        Relative path of the artifact.

    Returns
    -------
    str
        One of ``raw_data``, ``processed_data``, ``model``, ``model_output``,
        ``evaluation``, or ``state``. If the directory is not recognised,
        ``unknown`` is returned.
    """
    mapping = {
        "data": {
            "raw": "raw_data",
            "processed": "processed_data",
        },
        "models": {
            "": "model",  # files directly under models/
        },
        "results": {
            "": "evaluation",
        },
        "state": {
            "": "state",
        },
    }

    parts = file_path.parts
    if not parts:
        return "unknown"

    top = parts[0]
    sub = parts[1] if len(parts) > 1 else ""

    if top in mapping:
        for key, typ in mapping[top].items():
            if key == sub or (key == "" and sub == ""):
                return typ
    return "unknown"

def get_artifact_metadata(file_path: Path) -> dict:
    """
    Produce the manifest dictionary for a given artifact file.

    The function computes the SHA‑256 checksum, infers the artifact type,
    and leaves optional fields (description, generated_by) empty – they can
    be filled manually later.

    Parameters
    ----------
    file_path: Path
        Relative path to the artifact.

    Returns
    -------
    dict
        Dictionary matching the manifest schema for a single artifact.
    """
    checksum = compute_checksum(file_path)
    artifact_type = infer_artifact_type(file_path)

    return {
        "path": str(file_path),
        "type": artifact_type,
        "description": "",
        "checksum": checksum,
        "generated_by": "",
    }

# -------------------------------------------------------------------------
# Core manifest updating logic
# -------------------------------------------------------------------------

def load_manifest(manifest_path: Path) -> dict:
    """
    Load the existing manifest YAML file. If the file does not exist, a
    minimal manifest structure is created.

    Parameters
    ----------
    manifest_path: Path
        Path to ``data/manifest.yaml``.

    Returns
    -------
    dict
        Parsed manifest content.
    """
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    # Create a fresh manifest skeleton
    return {
        "version": "1.0",
        "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "updated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "artifacts": [],
    }

def update_manifest(
    manifest_path: Path = Path("data/manifest.yaml"),
    repo_root: Path = Path("."),
) -> None:
    """
    Update the manifest file with correct checksums for all artifacts and
    add any missing entries.

    The function:
    1. Loads the existing manifest.
    2. Indexes current entries by their ``path``.
    3. Scans the repository for all artifact files.
    4. Updates checksum values for existing entries.
    5. Adds new entries for files not yet listed.
    6. Refreshes the ``updated_at`` timestamp.
    7. Writes the manifest back to disk.

    Parameters
    ----------
    manifest_path: Path, optional
        Path to the manifest file (default ``data/manifest.yaml``).
    repo_root: Path, optional
        Repository root directory (default current directory).
    """
    manifest = load_manifest(manifest_path)

    # Ensure the top‑level keys exist
    manifest.setdefault("artifacts", [])
    manifest.setdefault("version", "1.0")
    manifest.setdefault("created_at", datetime.utcnow().replace(microsecond=0).isoformat() + "Z")

    # Index existing artifacts by path for quick lookup
    existing_by_path = {entry["path"]: entry for entry in manifest["artifacts"]}

    # Discover all artifact files in the repository
    all_files = get_all_artifacts(repo_root)

    for rel_path in all_files:
        rel_str = str(rel_path)

        # Compute checksum for the current file
        checksum = compute_checksum(rel_path)

        if rel_str in existing_by_path:
            # Update only the checksum (preserve other fields)
            existing_by_path[rel_str]["checksum"] = checksum
        else:
            # Create a brand‑new manifest entry
            new_entry = get_artifact_metadata(rel_path)
            manifest["artifacts"].append(new_entry)

    # Refresh the updated_at timestamp
    manifest["updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # Write the updated manifest back to disk (sorted for deterministic output)
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, width=120)

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """
    Command‑line interface for the manifest updater.

    Usage
    -----
    ``python -m scripts.update_manifest``

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Currently we accept no arguments; future extensions could add
    # options such as ``--manifest`` or ``--root``.
    try:
        update_manifest()
    except Exception as exc:
        print(f"Error while updating manifest: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
