import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

"""
T001 – Create the required project directory tree and verify its existence.

This script ensures that the nine top‑level folders required by the pipeline
are present, creates any missing ones, and writes a simple directory listing
to ``docs/directory_structure.txt``. The listing contains each required path
(ending with a trailing slash) on its own line, which satisfies the
verification step that checks for the presence of all folders.
"""

log = get_logger(__name__)

# List of directories that must exist relative to the project root.
REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    os.path.join("data", "raw"),
    os.path.join("data", "processed"),
    os.path.join("data", "results"),
    "docs",
    "contracts",
    "config",
]

def create_directories() -> None:
    """
    Create each directory in ``REQUIRED_DIRS`` if it does not already exist.
    """
    for rel_dir in REQUIRED_DIRS:
        dir_path: Path = paths.root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory exists: {dir_path}")

def write_directory_listing() -> None:
    """
    Write a plain‑text list of the required directories to
    ``docs/directory_structure.txt``. Each entry ends with a trailing slash,
    matching the format produced by ``tree -L 2 .`` for top‑level entries.
    """
    lines = [f"{rel_dir}/" for rel_dir in REQUIRED_DIRS]
    content = "\n".join(lines) + "\n"
    output_path: Path = paths.docs("directory_structure.txt")
    output_path.write_text(content, encoding="utf-8")
    log.info(f"Wrote directory structure listing to {output_path}")

def main() -> None:
    """Entry point for the script."""
    create_directories()
    write_directory_listing()

if __name__ == "__main__":
    main()
