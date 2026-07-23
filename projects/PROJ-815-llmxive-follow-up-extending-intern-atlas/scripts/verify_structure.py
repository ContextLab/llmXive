"""
Script to verify the project structure exists as required by T001.
Run this script to confirm all directories and placeholder files are created.
"""
import os
import sys
from pathlib import Path

def main():
    base = Path("projects/PROJ-815-llmxive-follow-up-extending-intern-atlas")
    
    required_dirs = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration"
    ]

    required_files = [
        base / "code" / "__init__.py",
        base / "data" / "__init__.py",
        base / "tests" / "__init__.py",
        base / "code" / "data" / "__init__.py",
        base / "code" / "models" / "__init__.py",
        base / "code" / "analysis" / "__init__.py",
        base / "code" / "utils" / "__init__.py",
        base / "data" / "raw" / ".gitkeep",
        base / "data" / "processed" / ".gitkeep",
        base / "tests" / "unit" / "__init__.py",
        base / "tests" / "integration" / "__init__.py",
        base / "scripts" / "verify_structure.py"
    ]

    all_ok = True
    
    print(f"Verifying structure in: {base.absolute()}")
    
    # Check directories
    for d in required_dirs:
        dir_path = base / d
        if not dir_path.is_dir():
            print(f"MISSING DIR: {dir_path}")
            all_ok = False
        else:
            print(f"OK DIR: {dir_path}")
    
    # Check files
    for f in required_files:
        if not f.exists():
            print(f"MISSING FILE: {f}")
            all_ok = False
        else:
            print(f"OK FILE: {f}")

    if not all_ok:
        print("\n❌ Verification FAILED. Structure incomplete.")
        sys.exit(1)
    else:
        print("\n✅ Verification PASSED. All required structure exists.")
        sys.exit(0)

if __name__ == "__main__":
    main()