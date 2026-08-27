import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the code/ module.
    Specifically: simulation/, models/, metrics/, validation/, plots/, scripts/
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"

    subdirs = [
        "simulation",
        "models",
        "metrics",
        "validation",
        "plots",
        "scripts"
    ]

    created_paths = []
    for subdir in subdirs:
        target_path = code_dir / subdir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(target_path))
            print(f"Created directory: {target_path}")
        else:
            print(f"Directory already exists: {target_path}")

    # Ensure __init__.py files exist in each new directory to make them packages
    # This is crucial for imports like `from simulation.config import ...` to work
    for subdir in subdirs:
        init_file = code_dir / subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created package init: {init_file}")

    return created_paths

def main():
    """Entry point for the script."""
    print("Setting up code/ directory structure...")
    paths = create_directories()
    print(f"Setup complete. Created {len(paths)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())