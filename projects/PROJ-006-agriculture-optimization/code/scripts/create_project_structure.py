"""
Script to create the initial project directory structure for llmXive research projects.
Creates standard directories: src/, tests/, contracts/, data/ (with subdirs).
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the standard project structure."""
    # Determine project root (assuming this script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define required directories
    directories = [
        project_root / "src",
        project_root / "src" / "cli",
        project_root / "src" / "config",
        project_root / "src" / "data",
        project_root / "src" / "data" / "collectors",
        project_root / "src" / "data" / "generators",
        project_root / "src" / "data" / "processing",
        project_root / "src" / "models",
        project_root / "src" / "services",
        project_root / "src" / "analysis",
        project_root / "src" / "utils",
        project_root / "tests",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "tests" / "unit",
        project_root / "contracts",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        project_root / "data" / "remote-sensing",
        project_root / "reports",
        project_root / "specs",
        project_root / "docs",
    ]

    for directory in directories:
        ensure_dir(directory)
        print(f"Created: {directory.relative_to(project_root)}")

    print(f"\nProject structure created successfully in: {project_root}")

if __name__ == "__main__":
    main()
