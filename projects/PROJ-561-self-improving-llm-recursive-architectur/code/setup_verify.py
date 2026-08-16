"""
Verification script for project structure.
Checks existence of required directories and __init__.py files.
"""
import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verifies that all required directories and __init__.py files exist.
    Returns True if all checks pass, False otherwise.
    """
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    all_good = True
    missing_dirs = []
    missing_inits = []

    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            missing_dirs.append(str(full_path))
            all_good = False
            continue
        
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            missing_inits.append(str(init_file))
            all_good = False
        elif init_file.stat().st_size == 0:
            # Optional: warn if empty, but task says "initialize", so empty might be technically created but not initialized content-wise.
            # However, the task says "initialize __init__.py files", implying content.
            # Let's treat empty as missing for verification strictness.
            missing_inits.append(str(init_file))
            all_good = False

    if missing_dirs:
        print("MISSING DIRECTORIES:")
        for d in missing_dirs:
            print(f"  - {d}")
    
    if missing_inits:
        print("MISSING __init__.py FILES:")
        for f in missing_inits:
            print(f"  - {f}")

    if all_good:
        print("Project structure verification: PASSED")
    else:
        print("Project structure verification: FAILED")
    
    return all_good

if __name__ == "__main__":
    success = verify_project_structure()
    sys.exit(0 if success else 1)
