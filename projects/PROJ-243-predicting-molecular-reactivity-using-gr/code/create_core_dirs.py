"""
Script to create core project directories and place a .gitkeep file in each.
Also generates a listing of all .gitkeep files for verification.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_dir_with_gitkeep(dir_path: Path) -> None:
    """Create the directory (including parents) and an empty .gitkeep file."""
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    gitkeep.touch(exist_ok=True)

def main() -> None:
    # Define the core directories relative to the project root
    core_dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("assets"),
        paths.code(),
        paths.artifacts(),
        paths.tests(),
    ]

    # Create each directory and its .gitkeep file
    for d in core_dirs:
        _ensure_dir_with_gitkeep(d)
        log.info(f"Ensured directory and .gitkeep: {d}")

    # After creation, generate a simple verification file listing all .gitkeep paths
    root_path = paths.root
    gitkeep_files = sorted(p.relative_to(root_path).as_posix() for p in root_path.rglob(".gitkeep"))

    listing_path = paths.artifacts("directory_listing.txt")
    with listing_path.open("w", encoding="utf-8") as f:
        for rel_path in gitkeep_files:
            f.write(f"{rel_path}\n")

    log.info(f"Directory listing written to {listing_path}")

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        log.exception(f"Failed to create core directories: {exc}")
        sys.exit(1)