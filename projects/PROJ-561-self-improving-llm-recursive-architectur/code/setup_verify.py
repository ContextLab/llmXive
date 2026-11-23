"""
Project Structure Verification Script for llmXive Self-Improving LLM Pipeline.

This script verifies that the required directory structure and __init__.py
files exist as specified in the implementation plan.
"""
import os
import sys
from pathlib import Path

def verify_project_structure():
    """
    Verify the project directory structure and __init__.py files.
    
    Returns:
      tuple: (is_valid, missing_items)
        - is_valid: bool indicating if all required items exist
        - missing_items: list of strings describing missing items
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).parent.parent
    
    # Define the required directory structure relative to base_dir
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
        "code/schemas",
        "code/utils",
        "code/results",
        "code/scripts",
        "docs",
        "state",
        "logs"
    ]
    
    missing_items = []
    valid = True
    
    print(f"Verifying project structure in: {base_dir}")
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        
        if not full_path.exists():
            missing_items.append(f"Directory: {dir_path}")
            valid = False
            print(f"  [MISSING] Directory: {dir_path}")
        else:
            print(f"  [OK] Directory: {dir_path}")
            
        # Check for __init__.py in code and tests subdirectories
        if dir_path.startswith("code") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                missing_items.append(f"Missing __init__.py in {dir_path}")
                valid = False
                print(f"    [MISSING] __init__.py in {dir_path}")
            else:
                print(f"    [OK] __init__.py in {dir_path}")
    
    # Check root __init__.py files for top-level directories
    top_level_dirs = ["code", "tests", "data", "results", "specs"]
    for dir_name in top_level_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                missing_items.append(f"Missing __init__.py in {dir_name}")
                valid = False
                print(f"  [MISSING] __init__.py in {dir_name}")
            else:
                print(f"  [OK] __init__.py in {dir_name}")
        else:
            # Directory missing is already caught above
            pass
    
    if valid:
        print(f"\n[SUCCESS] Project structure verification passed.")
    else:
        print(f"\n[FAILURE] Project structure verification failed.")
        print(f"Missing items ({len(missing_items)}):")
        for item in missing_items:
            print(f"  - {item}")
    
    return valid, missing_items

if __name__ == "__main__":
    valid, missing = verify_project_structure()
    sys.exit(0 if valid else 1)
