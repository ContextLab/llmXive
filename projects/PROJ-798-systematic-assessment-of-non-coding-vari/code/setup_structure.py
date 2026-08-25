"""
Script to initialize the project directory structure as per T001.
This script ensures all required directories and package markers exist.
"""
import os
from pathlib import Path

def main():
    base = Path(__file__).resolve().parent.parent
    print(f"Initializing project structure at: {base}")

    # Define all required directories
    dirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for rel_dir in dirs:
        full_path = base / rel_dir
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")

        # Create __init__.py for Python packages
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            # Write a minimal marker
            init_file.write_text("# Auto-generated package marker\n")
            print(f"  -> Created {init_file}")

    # Ensure specific sub-packages in tests have init files
    test_subdirs = ["unit", "integration", "contract"]
    for subdir in test_subdirs:
        path = base / "tests" / subdir
        path.mkdir(parents=True, exist_ok=True)
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated package marker\n")
            print(f"Created/Verified: {init_file}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()