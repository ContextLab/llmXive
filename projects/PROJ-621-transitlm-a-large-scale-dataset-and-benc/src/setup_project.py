"""
Project Setup Script for PROJ-621-transitlm
Atomically generates the required directory structure.
"""
import os
import shutil
import sys
from pathlib import Path

# Define the directory structure to create relative to the project root
DIRECTORIES = [
    "src",
    "src/lib",
    "src/models",
    "src/analysis",
    "src/cli",
    "src/contracts",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "figures",
    "specs",
    "specs/001-map-free-transit-route-generation",
]

# Define files to create with initial content
FILES = {
    "src/__init__.py": "",
    "src/lib/__init__.py": "",
    "src/models/__init__.py": "",
    "src/analysis/__init__.py": "",
    "src/cli/__init__.py": "",
    "src/contracts/__init__.py": "",
    "tests/__init__.py": "",
    "tests/unit/__init__.py": "",
    "tests/integration/__init__.py": "",
    "tests/contract/__init__.py": "",
    "data/.gitkeep": "",
    "data/raw/.gitkeep": "",
    "data/processed/.gitkeep": "",
    "data/results/.gitkeep": "",
    "figures/.gitkeep": "",
    "specs/.gitkeep": "",
    "specs/001-map-free-transit-route-generation/.gitkeep": "",
    ".gitkeep": "",
}

def get_project_root() -> Path:
    """Determine the project root directory."""
    # If run directly, assume current directory is the root
    # If run as a module, try to find the parent of the script location
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return Path.cwd()

def create_directories(root: Path) -> None:
    """Create all required directories."""
    created = []
    for dir_path in DIRECTORIES:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    return created

def create_files(root: Path) -> None:
    """Create all required empty or initialized files."""
    created = []
    for file_path, content in FILES.items():
        full_path = root / file_path
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            created.append(file_path)
    return created

def main() -> int:
    """Main entry point for the setup script."""
    root = get_project_root()
    print(f"Setting up project structure in: {root}")

    try:
        dirs = create_directories(root)
        files = create_files(root)

        print(f"Created {len(dirs)} directories:")
        for d in dirs:
            print(f"  - {d}")

        print(f"Created {len(files)} files:")
        for f in files:
            print(f"  - {f}")

        print("\nProject structure generation complete.")
        return 0

    except Exception as e:
        print(f"\nError during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
