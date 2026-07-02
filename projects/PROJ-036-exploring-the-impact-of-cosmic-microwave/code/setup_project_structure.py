import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Create the standard project directory structure for llmXive research projects.
    
    Creates:
    - code/
    - data/raw/
    - data/processed/
    - data/interim/
    - figures/
    - state/
    - contracts/
    - config/
    - specs/
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "figures",
        "state",
        "contracts",
        "config",
        "specs",
        "code/utils",
        "code/tests",
        "code/tools",
    ]
    
    for dir_path in directories:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files(root_path: Path) -> None:
    """
    Create __init__.py files in code directories to make them Python packages.
    """
    package_dirs = [
        "code",
        "code/utils",
        "code/tests",
        "code/tools",
    ]
    
    for dir_path in package_dirs:
        init_file = root_path / dir_path / "__init__.py"
        init_file.touch()
        print(f"Created init file: {init_file}")

def create_readme_files(root_path: Path) -> None:
    """
    Create README.md files for key directories explaining their purpose.
    """
    readmes = {
        "data/raw": "Raw data files downloaded from external sources. Do not modify.",
        "data/processed": "Processed and cleaned data ready for analysis.",
        "data/interim": "Intermediate data files during processing pipelines.",
        "figures": "Generated plots, charts, and visualizations.",
        "state": "Project state files, including artifact hashes and versioning info.",
        "contracts": "Schema contracts and validation rules for data outputs.",
        "config": "Configuration files for simulations and analysis parameters.",
        "specs": "Research specifications, design documents, and user stories.",
    }
    
    for dir_path, description in readmes.items():
        readme_file = root_path / dir_path / "README.md"
        if not readme_file.exists():
            content = f"# {dir_path}\n\n{description}\n\nThis directory is managed automatically by the project pipeline.\n"
            readme_file.write_text(content)
            print(f"Created README: {readme_file}")

def main() -> None:
    """
    Main entry point for creating the project structure.
    """
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Creating project structure at: {project_root}")
    
    create_directory_structure(project_root)
    create_init_files(project_root)
    create_readme_files(project_root)
    
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()