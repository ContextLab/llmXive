"""
generate_manifest.py
--------------------
Generates a reproducibility manifest `manifest.json` at the project root.

The manifest includes:
  * Exact Git commit hash of the repository (or "N/A" if unavailable)
  * URLs of the primary datasets used in the project
  * Software versions derived from `code/requirements.txt`
  * SHA‑256 checksums for **all** files in the repository (excluding the manifest itself)

The script is intended to be run from the repository root (or any sub‑directory)
via:
    python code/generate_manifest.py

It writes `manifest.json` in the repository root. The script exits with a
non‑zero status if a fatal error occurs (e.g., inability to write the file).
"""

import json
import subprocess
import hashlib
import os
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
    directory is not a Git repository, return ``"N/A"``.
    """
    try:
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
                versions[line] = None
    return versions

def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a single file.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_all_checksums(root: Path) -> list:
    """
    Walk the repository tree (starting at ``root``) and compute SHA‑256
    checksums for every regular file. The returned list contains strings
    of the form ``"<relative_path>:<sha256>"``.
    The manifest file itself (``manifest.json``) is excluded to avoid
    circular dependencies.
    """
    checksums = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            file_path = Path(dirpath) / fname
            # Skip the manifest we are about to write (if it already exists)
            if file_path.name == "manifest.json":
                continue
            # Skip hidden files like .gitkeep or editor backups if desired
            # (not required by the spec, so we include everything else)
            rel_path = file_path.relative_to(root).as_posix()
            try:
                file_hash = compute_file_sha256(file_path)
                checksums.append(f"{rel_path}:{file_hash}")
            except Exception as e:
                # If a file cannot be read, report the issue but continue.
                sys.stderr.write(f"Warning: could not checksum {rel_path}: {e}\\n")
    return checksums

def load_checksums(checksum_path: Path, root: Path) -> list:
    """
    Load the checksum manifest (typically ``data/checksums.txt``) and
    return a list of its lines. If the file does not exist or is empty,
    compute checksums for the entire repository on the fly.
    """
    if checksum_path.is_file():
        with checksum_path.open("r", encoding="utf-8") as fh:
            lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
        if lines:
            return lines

    # Fallback: compute checksums dynamically
    return compute_all_checksums(root)

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

    # 4. Checksums (read existing file or compute)
    checksum_path = root / "data" / "checksums.txt"
    checksums = load_checksums(checksum_path, root)

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