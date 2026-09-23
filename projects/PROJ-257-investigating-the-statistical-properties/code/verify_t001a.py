import os
import sys
from pathlib import Path

def verify_t001a():
    """
    Verify that all required directories for T001 exist.
    Returns True if all pass, False otherwise.
    """
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    all_passed = True
    
    print("Verifying directory structure for T001...")
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.is_dir():
            print(f"  [PASS] {dir_path} exists.")
        else:
            print(f"  [FAIL] {dir_path} does NOT exist.")
            all_passed = False
    
    # Verify .gitkeep files in specific locations
    gitkeep_checks = [
        "src/data/.gitkeep",
        "src/analysis/.gitkeep",
        "src/viz/.gitkeep",
        "src/utils/.gitkeep",
        "tests/.gitkeep",
        "tests/unit/.gitkeep",
        "tests/integration/.gitkeep",
        "tests/contract/.gitkeep",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "output/results/.gitkeep",
        "output/figures/.gitkeep"
    ]
    
    for file_path in gitkeep_checks:
        path = Path(file_path)
        if path.is_file():
            print(f"  [PASS] {file_path} exists.")
        else:
            print(f"  [FAIL] {file_path} does NOT exist.")
            all_passed = False
    
    if all_passed:
        print("\nVerification PASSED: All required directories and files exist.")
    else:
        print("\nVerification FAILED: Some directories or files are missing.")
        
    return all_passed

if __name__ == "__main__":
    success = verify_t001a()
    sys.exit(0 if success else 1)