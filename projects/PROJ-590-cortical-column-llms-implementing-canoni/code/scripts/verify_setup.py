"""
Verify project setup: Ensure all directories from T001 exist and state/template.yaml is present.
Exit 0 if all present, exit 1 otherwise.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"Checking project root: {project_root}")

    # Directories defined in T001
    required_dirs = [
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
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing_dirs.append(dir_path)
        else:
            print(f"  [OK] {dir_path}/")

    # Check state/template.yaml
    template_path = project_root / "state" / "template.yaml"
    if not template_path.is_file():
        missing_dirs.append("state/template.yaml")
    else:
        print(f"  [OK] state/template.yaml")

    if missing_dirs:
        print("\n[ERROR] Missing required paths:")
        for item in missing_dirs:
            print(f"  - {item}")
        print("\nSetup verification FAILED.")
        sys.exit(1)

    print("\nSetup verification PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()