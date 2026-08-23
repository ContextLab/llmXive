"""
Script to initialize the project directory structure for the llmXive pipeline.
Creates required directories and placeholder files (.gitkeep) to ensure
they are tracked by git.
"""
import os
import sys
from pathlib import Path

def create_structure():
    """Create the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    # Define directories to create
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "docs",
        "specs",
        "contracts",
        ".github/workflows"
    ]

    created = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            # Create .gitkeep in data directories to ensure they are tracked
            if dir_name.startswith("data/"):
                keep_file = dir_path / ".gitkeep"
                keep_file.touch()
                created.append(str(keep_file))
        else:
            # Ensure .gitkeep exists even if dir already existed
            if dir_name.startswith("data/"):
                keep_file = dir_path / ".gitkeep"
                if not keep_file.exists():
                    keep_file.touch()
                    created.append(str(keep_file))

    if created:
        print("Created directories and placeholders:")
        for p in created:
            print(f"  - {p}")
    else:
        print("All required directories already exist.")

    return True

def main():
    """Entry point for the script."""
    try:
        success = create_structure()
        if success:
            print("\nProject structure initialization complete.")
            sys.exit(0)
        else:
            print("\nProject structure initialization failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
