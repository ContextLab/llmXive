"""
Setup script to create the project directory structure.
Implements T001a, T001b, and T001c.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # T001a: Create src/ with subdirectories
    src_dirs = [
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils"
    ]
    for d in src_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {root / d}")
    
    # T001b: Create tests/ at repository root
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    # Create an __init__.py to make it a package
    (tests_dir / "__init__.py").touch()
    print(f"Created: {tests_dir}")
    
    # T001c: Create data/ (raw, processed) and output/ (results, figures)
    data_dirs = [
        "data/raw",
        "data/processed"
    ]
    output_dirs = [
        "output/results",
        "output/figures"
    ]
    
    for d in data_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {root / d}")
        
    for d in output_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"Created: {root / d}")
        
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()