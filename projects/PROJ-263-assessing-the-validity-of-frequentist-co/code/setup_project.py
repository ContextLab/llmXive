import os
import sys
from pathlib import Path

def create_structure(base_dir: Path) -> None:
    """
    Create the project directory structure for PROJ-263.
    
    Creates the following hierarchy relative to base_dir:
    - code/
    - data/raw/
    - data/processed/
    - data/external/
    - outputs/
    - figures/
    - tests/unit/
    - tests/integration/
    - specs/
    - docs/
    
    Adds .gitkeep files to data directories to ensure they are tracked by git.
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/external",
        "outputs",
        "figures",
        "tests/unit",
        "tests/integration",
        "specs",
        "docs",
    ]

    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create .gitkeep files in data directories
    data_dirs = ["data/raw", "data/processed", "data/external"]
    for dir_path in data_dirs:
        full_path = base_dir / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("")
            print(f"Created .gitkeep in: {full_path}")

    # Create README.md if it doesn't exist
    readme_path = base_dir / "README.md"
    if not readme_path.exists():
        readme_content = """# PROJ-263: Assessing the Validity of Frequentist Confidence Intervals

This project assesses the validity of frequentist confidence intervals with small sample sizes using real UCI datasets.

## Project Structure

- `code/`: Source code for simulations, coverage checks, and sensitivity analysis
- `data/raw/`: Raw UCI datasets downloaded from external sources
- `data/processed/`: Processed data and population means
- `outputs/`: Generated reports and aggregate results
- `figures/`: Generated plots and visualizations
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents
- `docs/`: Documentation

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run setup: `python code/setup_project.py`
3. Execute simulation: `python code/main.py`

## License

MIT License
"""
        readme_path.write_text(readme_content)
        print(f"Created README.md in: {base_dir}")

def main():
    """Main entry point for project structure creation."""
    # Determine the project root based on the script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # Go up one level from code/

    print(f"Creating project structure at: {project_root}")
    create_structure(project_root)
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()