import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created:
      - code/
      - data/raw/
      - data/derived/
      - tests/
      - tests/unit/
      - tests/integration/
      - tests/contract/
      - specs/
      - figures/
    """
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-gene-regulation",
        "figures",
        "logs"
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path.relative_to(root)}")
    
    # Create __init__.py files to ensure Python treats them as packages
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
        "data/__init__.py",
        "data/raw/__init__.py",
        "data/derived/__init__.py",
        "specs/001-gene-regulation/__init__.py"
    ]
    
    for init_file in init_files:
        full_path = root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty package file: {init_file}")
        else:
            print(f"Package file already exists: {init_file}")

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    main()