import os
import sys
from pathlib import Path

def main() -> None:
    """
    Create the full project directory tree for PROJ-191 in a single atomic operation.
    
    This script ensures the existence of the following structure relative to the project root:
    - code/
    - tests/
    - data/
    - docs/
    - code/data/
    - code/models/
    - code/inference/
    - code/robustness/
    - code/utils/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/contract/
    - tests/integration/
    """
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-191-investigating-the-validity-of-the-invers"
    
    # Define the target directory for this project
    target_dir = project_root / project_name
    
    # Define all required subdirectories relative to the target project directory
    required_dirs = [
        "code",
        "tests",
        "data",
        "docs",
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    print(f"Creating directory tree for: {project_name}")
    print(f"Target base: {target_dir}")
    
    created_count = 0
    for dir_name in required_dirs:
        full_path = target_dir / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  Created: {full_path.relative_to(target_dir)}")
        else:
            # Verify it is indeed a directory
            if full_path.is_dir():
                print(f"  Exists: {full_path.relative_to(target_dir)}")
            else:
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Ensure the __init__.py files exist in code and tests subdirectories to make them packages
    # This is a common requirement for Python projects, though not explicitly in the task description,
    # it ensures the structure is valid for imports later.
    init_paths = [
        target_dir / "code" / "__init__.py",
        target_dir / "tests" / "__init__.py",
        target_dir / "code" / "data" / "__init__.py",
        target_dir / "code" / "models" / "__init__.py",
        target_dir / "code" / "inference" / "__init__.py",
        target_dir / "code" / "robustness" / "__init__.py",
        target_dir / "code" / "utils" / "__init__.py",
        target_dir / "tests" / "unit" / "__init__.py",
        target_dir / "tests" / "contract" / "__init__.py",
        target_dir / "tests" / "integration" / "__init__.py",
    ]
    
    for init_path in init_paths:
        if not init_path.exists():
            init_path.touch()
            # Add a docstring to avoid empty file warnings if desired, 
            # but an empty file is valid Python.
            print(f"  Initialized: {init_path.relative_to(target_dir)}")
    
    print(f"\nDirectory tree creation complete. {created_count} new directories created.")
    print(f"Total directories ensured: {len(required_dirs)}")

if __name__ == "__main__":
    main()