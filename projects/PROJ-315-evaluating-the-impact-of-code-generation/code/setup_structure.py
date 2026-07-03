"""
Script to initialize the project directory structure.
This script ensures that the required folders (code, data, docs, tests)
and necessary __init__.py files exist.
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: Path):
    """Create the main project directories."""
    dirs = [
        root_dir / "code",
        root_dir / "data",
        root_dir / "docs",
        root_dir / "tests",
        root_dir / "contracts",
        root_dir / "docs" / "reports",
        root_dir / "code" / "utils",
        root_dir / "code" / "data",
        root_dir / "code" / "labeling",
        root_dir / "code" / "analysis",
        root_dir / "code" / "report",
        root_dir / "tests" / "unit",
        root_dir / "tests" / "integration",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

def create_init_files(root_dir: Path):
    """Create __init__.py files for all packages."""
    packages = [
        "code",
        "code/utils",
        "code/data",
        "code/labeling",
        "code/analysis",
        "code/report",
        "data",
        "docs",
        "tests",
        "tests/unit",
        "tests/integration",
        "contracts",
    ]
    for pkg in packages:
        path = root_dir / pkg / "__init__.py"
        if not path.exists():
          with open(path, "w", encoding="utf-8") as f:
              f.write('"""\n' + pkg + " package.\n\"\"\"\n")
          print(f"Created init file: {path}")

def create_readme_files(root_dir: Path):
    """Create placeholder README files for directories."""
    readmes = {
        "code": "Source code for the research pipeline.",
        "data": "Datasets and processed data artifacts.",
        "docs": "Documentation and research reports.",
        "tests": "Test suites for the project.",
        "contracts": "Data schemas and API contracts.",
    }
    for folder, desc in readmes.items():
        path = root_dir / folder / "README.md"
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {folder.capitalize()}\n\n{desc}\n")
            print(f"Created README: {path}")

def main():
    """Main entry point to setup the project structure."""
    root = Path.cwd()
    print(f"Initializing project structure in: {root}")
    create_directory_structure(root)
    create_init_files(root)
    create_readme_files(root)
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()