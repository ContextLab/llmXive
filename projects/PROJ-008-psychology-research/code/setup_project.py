import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure the directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {path}")

def main() -> int:
    """Create the required project sub-directories for code and tests."""
    project_root = Path(__file__).resolve().parent.parent
    base_path = project_root / "projects" / "PROJ-008-psychology-research"

    if not base_path.exists():
        print(f"Error: Base project directory not found: {base_path}")
        return 1

    # Define the directories required by T001c
    code_dirs = [
        base_path / "code" / "data",
        base_path / "code" / "analysis",
        base_path / "code" / "viz",
        base_path / "code" / "utils",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
    ]

    created_count = 0
    for dir_path in code_dirs:
        try:
            ensure_dir(dir_path)
            print(f"Created/Verified: {dir_path.relative_to(project_root)}")
            created_count += 1
        except Exception as e:
            print(f"Error creating {dir_path.relative_to(project_root)}: {e}")
            return 1

    print(f"Successfully ensured {created_count}/{len(code_dirs)} directories exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
