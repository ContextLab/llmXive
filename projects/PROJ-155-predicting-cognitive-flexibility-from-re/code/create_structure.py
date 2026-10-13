"""
Create the required directory structure for the project.
"""
import os
from pathlib import Path
from llmxive_toolkit import paths

def ensure_dir(path: Path) -> None:
    """Ensure that path exists as a directory."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the required directory structure."""
    dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.figures(),
        paths.docs(),
        paths.path("tests"),
        paths.path("data", "logs"),
    ]
    for d in dirs:
        ensure_dir(d)
    print("Directory structure created successfully.")

if __name__ == "__main__":
    main()
