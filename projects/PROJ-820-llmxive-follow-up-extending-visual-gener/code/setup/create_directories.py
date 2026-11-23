import os
import sys
from pathlib import Path
from typing import List

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """
    Initialize project structure by creating all required directories
    defined in plan.md for the llmXive follow-up project.
    """
    # Define the project root (assumed to be the directory containing this script's parent 'code')
    # However, to be robust, we assume the script is run from the project root or we derive it.
    # Based on standard conventions, we will assume the script is run from the project root.
    # If run as a module, we need to find the project root.
    # For this task, we assume the current working directory is the project root.
    project_root = Path.cwd()

    # Define all required directories
    required_dirs: List[Path] = [
        # Data directories
        project_root / "data" / "raw",
        project_root / "data" / "derived" / "physics_constraints",
        project_root / "data" / "derived" / "prompts",
        project_root / "data" / "derived" / "generated_images",
        project_root / "data" / "derived" / "evaluation_results",
        project_root / "data" / "processed",
        
        # Code directories
        project_root / "code" / "simulation",
        project_root / "code" / "generation",
        project_root / "code" / "evaluation",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        
        # Test directories
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "tests" / "unit",
        
        # Specs directories
        project_root / "specs" / "001-llmxive-followup",
        project_root / "specs" / "001-llmxive-followup" / "contracts",
        
        # State directories
        project_root / "state" / "projects",
    ]

    print(f"Initializing project structure at: {project_root}")
    
    created_count = 0
    for dir_path in required_dirs:
        create_directory(dir_path)
        created_count += 1

    print(f"Project initialization complete. Created/Verified {created_count} directories.")

if __name__ == "__main__":
    main()
