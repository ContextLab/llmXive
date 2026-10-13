"""
Simple utility to create the required directory structure for the project.
This script is not automatically invoked by the pipeline but can be
run manually if the folders are missing.
"""
from pathlib import Path

from llmxive_toolkit import paths


def ensure_dir(path: Path) -> None:
    """
    Ensure that *path* exists as a directory.
    """
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Create all top‑level directories required by the specification.
    """
    for sub in [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "docs",
        "tests",
    ]:
        ensure_dir(paths.path(sub))

if __name__ == "__main__":
    main()
