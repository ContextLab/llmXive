"""
Project Structure Setup Module.
Creates the required directory hierarchy and placeholder files for the
PROJ-532-predicting-material-degradation-pathways project.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def create_placeholder_file(path: Path, content: str = "") -> None:
    """Create a file with optional initial content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)

def main() -> None:
    """
    Execute the full project structure setup.
    Creates directories under the project root relative to the current working directory.
    """
    # Base project root
    project_root = Path.cwd() / "projects" / "PROJ-532-predicting-material-degradation-pathways"
    ensure_dir(project_root)

    # Core directories
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/contracts",
        "tests/unit",
        "tests/integration",
        "results/metrics",
        "results/plots",
        "results/artifacts",
        "specs",
        "figures",
    ]

    for d in dirs:
        ensure_dir(project_root / d)

    # Create README.md in project root
    readme_content = """# PROJ-532: Predicting Material Degradation Pathways

This project implements an automated pipeline for predicting material degradation pathways
from compositional data.

## Structure
- `code/`: Source code modules
- `data/`: Raw, processed, and contract data
- `tests/`: Unit and integration tests
- `results/`: Model artifacts, metrics, and plots
- `specs/`: Feature specifications and design documents
"""
    create_placeholder_file(project_root / "README.md", readme_content)

    # Create README.md in data directories
    data_readme = """# Data Directory

This directory stores raw and processed data for the project.

## Subdirectories
- `raw/`: Original downloaded datasets
- `processed/`: Cleaned and preprocessed data ready for modeling
- `contracts/`: Derived contracts and reference vectors (e.g., literature vectors, alloy maps)
"""
    create_placeholder_file(project_root / "data" / "README.md", data_readme)

    # Create README.md in results directories
    results_readme = """# Results Directory

This directory stores model outputs, metrics, and visualizations.

## Subdirectories
- `metrics/`: JSON reports on model performance and validation
- `plots/`: Generated visualizations (PNG, SVG)
- `artifacts/`: Saved model objects (pkl) and pipelines
"""
    create_placeholder_file(project_root / "results" / "README.md", results_readme)

    # Create __init__.py files to make directories Python packages
    init_files = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    for f in init_files:
        create_placeholder_file(project_root / f / "__init__.py", "# Package initialization")

    print(f"Project structure created at: {project_root}")
    print("Directories created:")
    for d in dirs:
        print(f"  - {project_root / d}")

if __name__ == "__main__":
    main()