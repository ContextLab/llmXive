import os
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def create_directories() -> None:
    """Create the required subdirectories for the project structure."""
    root = get_project_root()
    
    directories = [
        root / "data" / "processed",
        root / "artifacts",
        root / "tests" / "contract",
        root / "tests" / "integration",
        root / "tests" / "unit",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main() -> None:
    """Entry point for directory creation script."""
    create_directories()
    print("Directory setup complete.")

if __name__ == "__main__":
    main()
