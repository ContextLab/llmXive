"""
generate_manifest.py
--------------------
Generates a reproducibility manifest `manifest.json` at the project root.

The manifest includes:
  * Exact Git commit hash of the repository (or "N/A" if unavailable)
  * URLs of the primary datasets used in the project
  * Software versions derived from `code/requirements.txt`
  * All checksum entries from the project's checksum manifest (if present)

The script is intended to be run from the repository root (or any sub‑directory)
via:
    python code/generate_manifest.py

It writes `manifest.json` in the repository root. The script exits with a
non‑zero status if a fatal error occurs (e.g., inability to write the file).
"""

import json
import subprocess
from pathlib import Path
import sys

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def get_project_root() -> Path:
    """
    Return the absolute path to the repository root (the directory that
    contains this script's grand‑parent folder).
    """
    # This file lives in <repo_root>/code/generate_manifest.py
    return Path(__file__).resolve().parents[1]

def get_git_commit_hash(root: Path) -> str:
    """
    Retrieve the current Git commit hash. If Git is unavailable or the
    directory is not a Git repository, return ``\"N/A\"``.
    """
    try:
        # Use ``git rev-parse HEAD`` relative to the repository root.
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL
        )
        return commit.decode().strip()
    except Exception:
        return "N/A"

def parse_requirements(req_path: Path) -> dict:
    """
    Parse ``requirements.txt`` into a mapping ``{package: version}``. Lines
    that do not contain an explicit version are stored with a ``None`` value.
    """
    versions = {}
    if not req_path.is_file():
        return versions

    with req_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                versions[pkg.strip()] = ver.strip()
            else:
                # No pinned version – store the raw spec.
                versions[line] = None
    return versions

def load_checksums(checksum_path: Path) -> list:
    """
    Load the checksum manifest (typically ``data/checksums.txt``) and
    return a list of its lines. If the file does not exist, return an
    empty list.
    """
    if not checksum_path.is_file():
        return []
    with checksum_path.open("r", encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh]

# -------------------------------------------------------------------------
# Main manifest generation
# -------------------------------------------------------------------------

def build_manifest() -> dict:
    """
    Assemble the manifest dictionary.
    """
    root = get_project_root()

    # 1. Git commit hash
    commit_hash = get_git_commit_hash(root)

    # 2. Dataset URLs (canonical sources)
    datasets = {
        "openneuro_ds001495": "https://openneuro.org/datasets/ds001495",
        "rocstories": "https://huggingface.co/datasets/jamestran/roc_stories",
    }

    # 3. Software versions from requirements.txt
    req_path = root / "code" / "requirements.txt"
    software_versions = parse_requirements(req_path)

    # 4. Checksums (if the checksum utility has already run)
    checksum_path = root / "data" / "checksums.txt"
    checksums = load_checksums(checksum_path)

    manifest = {
        "commit_hash": commit_hash,
        "datasets": datasets,
        "software_versions": software_versions,
        "checksums": checksums,
    }
    return manifest

def write_manifest(manifest: dict, output_path: Path) -> None:
    """
    Write the manifest as pretty‑printed JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

def main() -> None:
    """
    Entry point for the script.
    """
    root = get_project_root()
    manifest = build_manifest()
    manifest_path = root / "manifest.json"
    try:
        write_manifest(manifest, manifest_path)
        print(f"Reproducibility manifest written to {manifest_path}")
    except Exception as exc:
        sys.stderr.write(f"Failed to write manifest: {exc}\\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
