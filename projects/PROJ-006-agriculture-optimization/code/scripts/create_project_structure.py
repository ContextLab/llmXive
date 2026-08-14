"""
Script to create the project directory structure for llmXive PROJ-006.
Creates src/, tests/, contracts/, data/, and subdirectories as per plan.md.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the full project structure."""
    # Determine project root (parent of scripts/)
    project_root = Path(__file__).resolve().parent.parent

    # Define directory structure
    directories = [
        "src",
        "src/cli",
        "src/config",
        "src/data",
        "src/data/collectors",
        "src/data/processing",
        "src/utils",
        "src/analysis",
        "src/services",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "contracts",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "data/remote-sensing",
        "reports",
        "figures",
        "docs",
        "specs",
    ]

    for dir_path in directories:
        ensure_dir(project_root / dir_path)

    # Create __init__.py files for Python packages
    package_dirs = [
        "src",
        "src/cli",
        "src/config",
        "src/data",
        "src/data/collectors",
        "src/data/processing",
        "src/utils",
        "src/analysis",
        "src/services",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for dir_path in package_dirs:
        init_file = project_root / dir_path / "__init__.py"
        init_file.touch(exist_ok=True)

    print(f"Project structure created at: {project_root}")

if __name__ == "__main__":
    main()
