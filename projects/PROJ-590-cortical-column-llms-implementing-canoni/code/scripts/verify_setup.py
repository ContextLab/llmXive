"""
T004: Verify Setup
Confirms all directories from T001 exist and state/template.yaml is present.
Exits 0 if all present, exits 1 otherwise.
"""
import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Determine the project root (parent of 'code' directory)."""
    current = Path(__file__).resolve()
    # Navigate up from code/scripts to project root
    if current.name == "verify_setup.py" and current.parent.name == "scripts":
        return current.parent.parent
    return current.parent.parent

def verify_setup() -> bool:
    """
    Verify the existence of required directories and files.
    Returns True if all checks pass, False otherwise.
    """
    project_root = get_project_root()
    required_dirs = [
        "src",
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
    ]

    missing_dirs = []
    for d in required_dirs:
        path = project_root / d
        if not path.is_dir():
            missing_dirs.append(str(path))

    if missing_dirs:
        print("ERROR: Missing required directories:")
        for d in missing_dirs:
            print(f"  - {d}")
        return False

    # Verify state/template.yaml
    template_path = project_root / "state" / "template.yaml"
    if not template_path.is_file():
        print(f"ERROR: Missing required file: {template_path}")
        return False

    print("SUCCESS: All required directories and state/template.yaml exist.")
    return True

def main():
    success = verify_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
