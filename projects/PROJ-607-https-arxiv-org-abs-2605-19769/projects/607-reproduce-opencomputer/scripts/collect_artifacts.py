"""
collect_artifacts.py

Copies generated artifacts from Docker output directories to a blinded review folder.
This script simulates the copy logic required for T022.
In a real Docker environment, this would execute `docker cp`.
Here, it handles local paths as a fallback for testing or when artifacts are already local.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
BLINDING_DIR = DATA_DIR / "blinded_artifacts"

# Allowed extensions for artifacts
ARTIFACT_EXTENSIONS = {".wav", ".docx", ".pdf", ".png", ".jpg", ".txt", ".csv"}


def find_artifacts(source_dir: Path) -> List[Path]:
    """Recursively find all artifact files in source directory."""
    artifacts = []
    if not source_dir.exists():
        return artifacts
    for root, _, files in os.walk(source_dir):
        for file in files:
            if Path(file).suffix.lower() in ARTIFACT_EXTENSIONS:
                artifacts.append(Path(root) / file)
    return artifacts


def copy_artifacts(source_dir: Path, dest_dir: Path) -> int:
    """Copy artifacts to destination, preserving relative structure."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    artifacts = find_artifacts(source_dir)
    if not artifacts:
        print(f"No artifacts found in {source_dir}")
        return 0

    copied_count = 0
    for src in artifacts:
        # Create a relative path to maintain structure
        rel_path = src.relative_to(source_dir)
        dest = dest_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
            copied_count += 1
            print(f"Copied: {src} -> {dest}")
        except Exception as e:
            print(f"Failed to copy {src}: {e}", file=sys.stderr)
    return copied_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect artifacts for blinded review.")
    parser.add_argument("--source", type=str, default=str(RESULTS_DIR), help="Source directory (e.g., Docker output mount)")
    parser.add_argument("--dest", type=str, default=str(BLINDING_DIR), help="Destination directory for blinded artifacts")
    args = parser.parse_args()

    source = Path(args.source)
    dest = Path(args.dest)

    if not source.exists():
        print(f"Error: Source directory does not exist: {source}", file=sys.stderr)
        return 1

    count = copy_artifacts(source, dest)
    print(f"Collection complete. {count} artifacts copied to {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())