"""
generate_manifest.py
--------------------

This script creates a reproducibility manifest `manifest.json` at the project root.
The manifest includes:

* Dataset URLs used in the project.
* The exact Git commit hash of the repository.
* Software versions extracted from `code/requirements.txt`.
* SHA‑256 checksums for every file in the repository (excluding typical
  non‑source directories such as ``.git``, ``.venv``/``venv`` and ``__pycache__``).

The script is intended to be run as part of the quick‑start pipeline:

```bash
python code/generate_manifest.py
```

It writes ``manifest.json`` to the repository root and exits with status 0
on success.  Any failure (e.g. missing Git, unreadable files) raises an
exception so the pipeline aborts loudly, satisfying the “fail loudly”
constraint.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import hashlib

# ----------------------------------------------------------------------
# Configuration – dataset URLs
# ----------------------------------------------------------------------
DATASET_URLS = {
    "openneuro_ds001495": "https://openneuro.org/datasets/ds001495",
    "rocstories": "https://huggingface.co/datasets/jamestran/roc_stories",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_git_commit_hash() -> str:
    """Return the current git commit hash (HEAD)."""
    try:
        # ``git`` must be available in the environment; otherwise raise.
        result = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.STDOUT
        )
        return result.decode().strip()
    except Exception as e:
        raise RuntimeError(f"Unable to obtain git commit hash: {e}")

def parse_requirements(req_path: Path) -> dict:
    """
    Parse a ``requirements.txt`` file and return a mapping of package -> version.
    Lines that are comments or empty are ignored. Only ``pkg==ver`` style
    specifications are captured (the pinned versions used throughout the project).
    """
    versions = {}
    if not req_path.is_file():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")
    with req_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Expected format: package==version
            if "==" in line:
                pkg, ver = line.split("==", 1)
                versions[pkg.strip()] = ver.strip()
            else:
                # If a line does not contain ``==`` we store the raw spec.
                versions[line] = None
    return versions

def sha256_checksum(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def collect_checksums(root: Path) -> dict:
    """
    Walk the repository tree and compute SHA‑256 checksums for every file.
    Certain directories are excluded because they contain transient,
    large, or environment‑specific data:

    * .git      – version‑control metadata
    * __pycache__ – compiled byte‑code
    * venv / .venv / .env – virtual‑environment directories
    * .ipynb_checkpoints – Jupyter checkpoints
    * data/raw – large raw neuroimaging downloads (optional but can be huge)
    * data/processed – large intermediate numpy files (optional)
    * data/results – large result artefacts (optional)

    The function can be tuned by editing ``EXCLUDE_DIRS``.
    """
    EXCLUDE_DIRS = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        ".env",
        ".ipynb_checkpoints",
        "data/raw",
        "data/processed",
        "data/results",
    }

    checksums = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # Convert to Path for easier handling
        dirpath = Path(dirpath)

        # Skip excluded top‑level directories
        rel_parts = dirpath.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            # Prevent descending into excluded sub‑trees
            dirnames[:] = []  # modify in‑place to prune walk
            continue

        for fname in filenames:
            file_path = dirpath / fname
            # Skip hidden files (e.g. .gitignore) – they are not source artefacts
            if fname.startswith("."):
                continue
            rel_path = file_path.relative_to(root).as_posix()
            try:
                checksum = sha256_checksum(file_path)
                checksums[rel_path] = checksum
            except Exception as e:
                raise RuntimeError(f"Failed to checksum {rel_path}: {e}")

    return checksums

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    project_root = Path(__file__).resolve().parents[1]  # repository root
    manifest_path = project_root / "manifest.json"

    # 1. Dataset URLs
    datasets = DATASET_URLS

    # 2. Git commit hash
    commit_hash = get_git_commit_hash()

    # 3. Software versions from requirements.txt
    req_path = project_root / "code" / "requirements.txt"
    software_versions = parse_requirements(req_path)

    # 4. Checksums for all relevant files
    checksums = collect_checksums(project_root)

    manifest = {
        "datasets": datasets,
        "commit_hash": commit_hash,
        "software_versions": software_versions,
        "checksums": checksums,
    }

    # Write JSON with pretty‑printing for readability
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"✅ Manifest written to {manifest_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.stderr.write(f"Error generating manifest: {exc}\\n")
        sys.exit(1)
