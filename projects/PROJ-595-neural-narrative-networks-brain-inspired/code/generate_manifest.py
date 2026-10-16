"""
generate_manifest.py

Generates a reproducibility manifest `manifest.json` at the project root.
The manifest includes:
  * Dataset URLs used in the project.
  * The exact Git commit hash of the repository.
  * Software versions extracted from `code/requirements.txt`.
  * SHA‑256 checksums for every regular file in the repository (excluding
    version‑control metadata and temporary artefacts).

The script is intended to be run as part of the quick‑start pipeline:
    python code/generate_manifest.py

It writes the manifest to the project root (same directory as this file)
using the `llmxive_toolkit.paths` helper to ensure the output directory
exists.
"""
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – dataset URLs (real, authoritative sources)
# ----------------------------------------------------------------------
DATASET_URLS = {
    "openneuro_ds001495": "https://openneuro.org/datasets/ds001495",
    "rocstories": "https://huggingface.co/datasets/jamestran/roc_stories",
}

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _git_commit_hash() -> str:
    """Return the current repository commit hash (SHA‑1)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        commit = result.stdout.strip()
        log.info(f"Detected git commit hash: {commit}")
        return commit
    except Exception as exc:
        log.error(f"Unable to obtain git commit hash: {exc}")
        raise RuntimeError("Git commit hash could not be determined.") from exc


def _parse_requirements(req_file: Path) -> Dict[str, str]:
    """
    Parse a ``requirements.txt`` file and return a mapping
    ``{package_name: version}``.  Only lines containing ``==`` are
    considered; comments and empty lines are ignored.
    """
    versions: Dict[str, str] = {}
    if not req_file.is_file():
        raise FileNotFoundError(f"Requirements file not found: {req_file}")

    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            pkg, ver = line.split("==", 1)
            versions[pkg.strip()] = ver.strip()
        else:
            # Packages without a pinned version are recorded as "unpinned"
            versions[line] = "unpinned"
    log.info(f"Parsed {len(versions)} package versions from {req_file}")
    return versions


def _sha256_checksum(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_checksums(root: Path) -> Dict[str, str]:
    """
    Walk the repository tree and compute SHA‑256 checksums for every
    regular file, returning a mapping of *relative* POSIX paths to their
    checksum strings.  Files inside ``.git`` or hidden directories are
    ignored.
    """
    checksums: Dict[str, str] = {}
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        # Skip version‑control metadata and typical temporary artefacts
        if any(part.startswith(".") for part in file_path.parts):
            continue
        rel_path = file_path.relative_to(root).as_posix()
        checksums[rel_path] = _sha256_checksum(file_path)
    log.info(f"Computed checksums for {len(checksums)} files.")
    return checksums


# ----------------------------------------------------------------------
# Main manifest generation
# ----------------------------------------------------------------------


def generate_manifest() -> Path:
    """
    Generate ``manifest.json`` at the repository root and return the
    path to the written file.
    """
    project_root = paths.root
    log.info(f"Project root resolved to: {project_root}")

    # 1. Dataset URLs
    datasets = DATASET_URLS

    # 2. Git commit hash
    commit_hash = _git_commit_hash()

    # 3. Software versions from requirements.txt
    requirements_path = paths.code("requirements.txt")
    software_versions = _parse_requirements(requirements_path)

    # 4. Checksums for all repository files
    checksums = _collect_checksums(project_root)

    manifest_content = {
        "datasets": datasets,
        "commit_hash": commit_hash,
        "software_versions": software_versions,
        "checksums": checksums,
    }

    manifest_path = project_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_content, indent=2, sort_keys=True))
    log.info(f"Reproducibility manifest written to {manifest_path}")
    return manifest_path


def main() -> None:
    """Entry‑point used when the script is executed directly."""
    try:
        generate_manifest()
    except Exception as exc:
        log.error(f"Failed to generate manifest: {exc}")
        raise


if __name__ == "__main__":
    main()
