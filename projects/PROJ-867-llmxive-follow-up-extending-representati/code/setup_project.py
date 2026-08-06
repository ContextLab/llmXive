import os
import sys
from pathlib import Path

def create_directory_structure(project_root: Path) -> None:
    """
    Creates the required directory structure for the project.
    Ensures code/, data/, tests/, docs/ exist under the project root.
    Also creates subdirectories for tests: unit/, contract/, integration/.
    """
    # Define the required subdirectories relative to the project root
    required_dirs = [
        "code",
        "data",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "docs",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure the directory is tracked by git
        # even if it's empty
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()

def main() -> None:
    """
    Entry point for creating the project directory structure.
    Expects to be run from the project root directory.
    """
    # The project root is the current working directory
    project_root = Path.cwd()
    
    print(f"Creating directory structure at: {project_root}")
    
    try:
        create_directory_structure(project_root)
        print("Directory structure created successfully.")
        
        # List the created structure for verification
        print("\nCreated structure:")
        for item in sorted(project_root.iterdir()):
            if item.is_dir() and item.name in ["code", "data", "tests", "docs"]:
                print(f"  {item.name}/")
                if item.name == "tests":
                    for sub in sorted(item.iterdir()):
                        if sub.is_dir():
                            print(f"    {sub.name}/")
                
    except Exception as e:
        print(f"Error creating directory structure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()