import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verify that all required directories and __init__.py files exist.
    
    Returns True if all checks pass, False otherwise.
    Prints verification results to stdout.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
        "results/logs",
        "results/figures",
        "data/checkpoints",
        "templates",
        "utils",
        "pipeline",
        "schemas",
        "scripts",
    ]
    
    # Directories that should have __init__.py
    python_package_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "utils",
        "pipeline",
        "schemas",
        "scripts",
        "results",
        "data",
    ]
    
    all_passed = True
    
    print("Verifying project structure...")
    print("=" * 50)
    
    # Check directories
    print("\nChecking directories:")
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ (MISSING)")
            all_passed = False
    
    # Check __init__.py files
    print("\nChecking __init__.py files:")
    for dir_path in python_package_dirs:
        full_path = base_dir / dir_path
        init_file = full_path / "__init__.py"
        if init_file.exists() and init_file.is_file():
            print(f"  ✓ {dir_path}/__init__.py")
        else:
            print(f"  ✗ {dir_path}/__init__.py (MISSING)")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All checks passed!")
    else:
        print("✗ Some checks failed. Please run setup_project.py first.")
    
    return all_passed

if __name__ == "__main__":
    success = verify_project_structure()
    sys.exit(0 if success else 1)
