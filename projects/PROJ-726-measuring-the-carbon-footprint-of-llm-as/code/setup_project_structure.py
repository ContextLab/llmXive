import os
import sys
from pathlib import Path


def create_directory_structure(root: Path) -> None:
    """
    Create the project directory structure required by the implementation plan.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/outputs/
    - tests/
    - output/
    
    Args:
        root: The project root directory path.
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests",
        "output",
    ]
    
    created = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            # Log if directory already exists but ensure parents exist
            dir_path.mkdir(parents=True, exist_ok=True)
    
    if created:
        print(f"Created directories:\n  {chr(10).join('  ' + p for p in created)}")
    else:
        print("All required directories already exist.")


def main() -> int:
    """
    Main entry point for the project structure setup script.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Determine project root (assumed to be the parent of 'code' if running from code/,
        # or current directory if running from root)
        if Path("code").exists():
            root = Path.cwd()
        else:
            root = Path.cwd().parent if (Path.cwd() / "code").exists() else Path.cwd()
        
        # Ensure we are in the project root by looking for a marker (e.g., tasks.md or plan.md)
        # If not found, default to current working directory
        if not (root / "tasks.md").exists() and not (root / "plan.md").exists():
            # Fallback: assume current directory is root
            root = Path.cwd()
        
        print(f"Project root detected at: {root}")
        create_directory_structure(root)
        return 0
    except Exception as e:
        print(f"Error creating directory structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
