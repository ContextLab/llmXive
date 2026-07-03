import os
import sys
from pathlib import Path

def get_repo_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the script is run from the project root or a subdirectory.
    """
    current = Path.cwd()
    # Simple heuristic: look for a marker file or just assume cwd is root if not deep
    # For robustness in this specific context, we assume the working directory IS the project root
    # or we traverse up to find a .git folder if it exists.
    if (current / ".git").exists():
        return current
    parent = current
    while parent != parent.parent:
        if (parent / ".git").exists():
            return parent
        parent = parent.parent
    return current

def create_directories(base_path: Path) -> None:
    """
    Creates the required directory structure for the project.
    """
    required_dirs = [
        "src",
        "data/raw",
        "data/processed",
        "scripts",
        "tests",
        "notebooks",
        "data/validation",
        "code",
        # Additional standard directories often needed
        "src/models",
        "src/generators",
        "src/config",
        "src/infrastructure",
        "data/validation/external",
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Directory initialization complete. Created {created_count} new directories.")

def main():
    """
    Entry point for the project initialization script.
    """
    root = get_repo_root()
    print(f"Initializing project structure at: {root}")
    create_directories(root)
    print("Done.")

if __name__ == "__main__":
    main()