import os
from pathlib import Path

def ensure_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    # Create .gitkeep to ensure empty directories are tracked by git
    gitkeep = p / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text(f"# {p.name} directory\n")

def main():
    """Initialize the project directory structure."""
    # Define the required directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/contracts",
        "code/prompts",
        "code/scripts",
        "code/tests",
        "specs",
    ]

    print("Creating project structure...")
    for dir_path in directories:
        ensure_directory(dir_path)
        print(f"  Created: {dir_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()