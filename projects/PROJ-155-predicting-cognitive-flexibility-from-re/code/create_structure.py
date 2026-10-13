"""
Creates the required directory structure for the project.
"""
import os
from pathlib import Path
from llmxive_toolkit import paths

def ensure_dir(path: Path) -> None:
    """Ensure that path exists as a directory."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the required directory structure."""
    # Use llmxive_toolkit.paths to ensure we are in the correct project root
    dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.docs(),
        paths.path("tests"),
    ]
    
    for d in dirs:
        ensure_dir(d)
        print(f"Ensured directory: {d}")

if __name__ == "__main__":
    main()
