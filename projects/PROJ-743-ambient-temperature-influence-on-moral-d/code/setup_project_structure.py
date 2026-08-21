import os
import sys
from pathlib import Path

def ensure_directories(base_path: Path) -> None:
    """
    Create the standard project directory structure.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - results/figures/
    - results/logs/
    - results/stats/
    - tests/
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests",
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Main entry point for project structure setup."""
    # Determine project root (assume script is in code/ or code/scripts/)
    script_path = Path(__file__).resolve()
    # If script is in code/, go up one level
    if script_path.parent.name == "code":
        project_root = script_path.parent.parent
    else:
        project_root = script_path.parent
    
    print(f"Setting up project structure at: {project_root}")
    ensure_directories(project_root)
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
