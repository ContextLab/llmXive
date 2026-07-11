import os
import sys
from pathlib import Path

def main():
    """
    Implements Task T001: Create project structure for PROJ-550.
    Creates the directory tree:
    projects/PROJ-550-exploring-the-convergence-of-iterated-fu/{
        code,
        data/raw,
        data/derived,
        tests/unit,
        tests/contract,
        docs
    }
    """
    project_root = Path("projects/PROJ-550-exploring-the-convergence-of-iterated-fu")
    subdirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests/unit",
        "tests/contract",
        "docs"
    ]

    created_dirs = []
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
        print(f"Created directory: {dir_path}")

    # Verify structure by listing contents
    print("\nProject structure verification:")
    for subdir in subdirs:
        dir_path = project_root / subdir
        if dir_path.exists() and dir_path.is_dir():
            # List immediate children to ensure non-empty (directories are non-empty by creation)
            print(f"  {dir_path}/ (exists)")
        else:
            print(f"  ERROR: {dir_path} missing!")
            return 1

    print(f"\nTask T001 completed successfully. Created {len(created_dirs)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
