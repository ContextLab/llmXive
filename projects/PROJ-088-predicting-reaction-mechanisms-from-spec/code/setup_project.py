import os
import sys
from pathlib import Path

# Project root relative to where this script runs (assumed to be code/ or root)
# We will resolve the project root as the parent of this file's directory if running from code/
# or the current directory if running from root.
def get_project_root() -> Path:
    """Determine the project root directory."""
    current_file = Path(__file__).resolve()
    # If running from code/setup_project.py, root is parent
    # If running from root, root is current
    if current_file.parent.name == "code":
        return current_file.parent.parent
    return current_file.parent

def create_directories(root: Path) -> None:
    """Create the required project directory structure."""
    dirs = [
        "src",
        "tests",
        "specs/001-predicting-reaction-mechanisms",
        "data",
        "state/projects",
        # Subdirectories for better organization (often needed for imports)
        "src/utils",
        "src/ingestion",
        "src/modeling",
        "src/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "data/reference",
        "figures",
        "state",
        "specs/contracts",
        "specs/feature",
    ]

    created = []
    for d in dirs:
        dir_path = root / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            # Ensure it is a directory
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")

    return created

def main():
    root = get_project_root()
    print(f"Project root detected at: {root}")
    created_dirs = create_directories(root)
    if created_dirs:
        print(f"Created {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"  - {d}")
    else:
        print("All required directories already exist.")

    # Verification listing
    print("\nVerifying directory structure:")
    required = [
        "src", "tests", "specs/001-predicting-reaction-mechanisms",
        "data", "state/projects"
    ]
    for r in required:
        p = root / r
        if p.exists() and p.is_dir():
            print(f"  [OK] {r}")
        else:
            print(f"  [FAIL] {r} - Missing or not a directory")
            sys.exit(1)

    print("\nDirectory structure setup complete.")

if __name__ == "__main__":
    main()