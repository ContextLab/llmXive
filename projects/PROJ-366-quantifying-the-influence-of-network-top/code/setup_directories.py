import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required code directory structure for the project.
    Directories created:
    - code/
    - code/ingest/
    - code/simulation/
    - code/metrics/
    - code/model/
    - code/analysis/
    """
    base_path = Path(__file__).resolve().parent.parent
    code_root = base_path / "code"

    directories = [
        code_root,
        code_root / "ingest",
        code_root / "simulation",
        code_root / "metrics",
        code_root / "model",
        code_root / "analysis",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    # Ensure __init__.py files exist to make them proper Python packages
    # This is crucial for the imports expected in the API surface
    init_files = [
        code_root / "__init__.py",
        code_root / "ingest" / "__init__.py",
        code_root / "simulation" / "__init__.py",
        code_root / "metrics" / "__init__.py",
        code_root / "model" / "__init__.py",
        code_root / "analysis" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file already exists: {init_file}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All directories already existed.")

    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)