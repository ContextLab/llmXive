import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verifies the existence of all required directories and __init__.py files
    for the project structure defined in T001.
    
    Returns:
        tuple: (success: bool, missing_dirs: list, missing_inits: list)
    """
    base_path = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
        "code/pipeline",
        "code/utils",
        "code/schemas",
        "code/results",
        "code/tests/unit",
        "code/tests/integration",
        "code/scripts",
        "data/logs",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(str(full_path))
    
    missing_inits = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            missing_inits.append(str(init_file))
    
    success = len(missing_dirs) == 0 and len(missing_inits) == 0
    return success, missing_dirs, missing_inits

if __name__ == "__main__":
    success, missing_dirs, missing_inits = verify_project_structure()
    if success:
        print("Project structure verification: PASSED")
        print("All required directories and __init__.py files exist.")
        sys.exit(0)
    else:
        print("Project structure verification: FAILED")
        if missing_dirs:
            print(f"Missing directories: {missing_dirs}")
        if missing_inits:
            print(f"Missing __init__.py files: {missing_inits}")
        sys.exit(1)
