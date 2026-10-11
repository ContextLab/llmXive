"""
setup_structure.py

Creates the project directory layout required by T001 and records a
structure manifest at ``data/results/structure_manifest.txt``.

The manifest lists every required directory as a project-relative path
(e.g. ``code/data_ingestion``, ``data/raw``, ``tests/unit``), sorted and
unique, so the CI verifier can check that all required directories exist.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

# Project root (paths.root is the project directory regardless of cwd)
ROOT = paths.root

REQUIRED_DIRS = [
    "code",
    "code/data_ingestion",
    "code/scoring",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/derived",
    "data/results",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def main() -> None:
    # Create every required directory
    for rel in REQUIRED_DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    # Collect all directories under code/, data/, tests/ as relative paths
    rel_dirs = set()
    for top in ("code", "data", "tests"):
        top_path = ROOT / top
        if not top_path.is_dir():
            continue
        rel_dirs.add(top)
        for p in top_path.rglob("*"):
            if p.is_dir():
                # Skip virtual environments and caches
                parts = p.relative_to(ROOT).parts
                if any(
                    seg in (".venv", "venv", "__pycache__", ".pytest_cache")
                    for seg in parts
                ):
                    continue
                rel_dirs.add(str(p.relative_to(ROOT)))

    # Verify every required directory exists
    missing = [rel for rel in REQUIRED_DIRS if not (ROOT / rel).is_dir()]
    if missing:
        raise RuntimeError(f"Missing required directories: {missing}")

    # Write the manifest (sorted, unique, one path per line)
    manifest_path = paths.data("results", "structure_manifest.txt")
    lines = sorted(rel_dirs)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Sanity check: manifest must contain all required directories
    written = set(manifest_path.read_text(encoding="utf-8").split())
    missing_in_manifest = [rel for rel in REQUIRED_DIRS if rel not in written]
    if missing_in_manifest:
        raise RuntimeError(
            f"Manifest is missing required directories: {missing_in_manifest}"
        )
    if len(written) < 11:
        raise RuntimeError(
            f"Manifest contains only {len(written)} unique directories; "
            "at least 11 are required."
        )

    print(f"Wrote {manifest_path} with {len(written)} unique directories.")
    print("Required directories present:", ", ".join(REQUIRED_DIRS))

if __name__ == "__main__":
    main()