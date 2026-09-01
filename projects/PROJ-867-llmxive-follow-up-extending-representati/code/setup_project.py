"""
Project setup module for creating the required directory structure.
"""
import os
import sys
from pathlib import Path


def create_directory_structure(base_path: str = None) -> Path:
    """
    Creates the project directory structure as per the implementation plan.
    
    Args:
        base_path: The base directory where the project structure will be created.
                   If None, uses the current working directory.
    
    Returns:
        Path: The path to the created project root directory.
    
    Raises:
        OSError: If directory creation fails.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    base = Path(base_path)
    
    # Project root directory name
    project_name = "PROJ-867-llmxive-follow-up-extending-representati"
    project_root = base / project_name
    
    # Required subdirectories
    required_dirs = [
        "code",
        "data",
        "tests",
        "docs",
        "specs",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "docs/contracts",
    ]
    
    # Create the project root
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Create all required subdirectories
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create a .gitkeep file in each directory to ensure they are tracked
    # even if they are empty (important for version control)
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
    
    # Create a README.md in the project root if it doesn't exist
    readme_path = project_root / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            f"# {project_name}\n\n"
            "Automated science pipeline for extending Representation Forcing "
            "for Structured Text Generation.\n\n"
            "## Directory Structure\n\n"
            "- `code/`: Source code\n"
            "- `data/`: Data files (raw, processed, results)\n"
            "- `tests/`: Test suites\n"
            "- `docs/`: Documentation\n"
            "- `specs/`: Specification documents\n"
            "- `figures/`: Generated figures and plots\n"
        )
    
    return project_root


def main():
    """
    Main entry point for the setup script.
    
    Creates the project directory structure and prints a summary.
    """
    try:
        project_root = create_directory_structure()
        print(f"✓ Project directory structure created at: {project_root}")
        
        # List the created directories
        print("\nCreated directories:")
        for item in sorted(project_root.iterdir()):
            if item.is_dir():
                print(f"  - {item.name}/")
        
        print("\n✓ Setup complete.")
        return 0
    except Exception as e:
        print(f"✗ Error creating directory structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
