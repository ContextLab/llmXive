import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure.
    
    Creates:
    - data/raw, data/interim, data/processed
    - code (already exists per T001c)
    - tests/unit, tests/integration (already exists per T001d)
    - reports (NEW for T001e)
    """
    root = Path(".")
    
    directories = [
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "processed",
        root / "reports",
    ]
    
    created = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    return created

def create_init_files():
    """
    Create __init__.py files in code and tests directories if they don't exist.
    """
    root = Path(".")
    
    init_paths = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "unit" / "__init__.py",
        root / "tests" / "integration" / "__init__.py",
    ]
    
    created = []
    for init_path in init_paths:
        if not init_path.exists():
            init_path.parent.mkdir(parents=True, exist_ok=True)
            init_path.touch()
            created.append(str(init_path))
            print(f"Created __init__.py: {init_path}")
        else:
            print(f"__init__.py already exists: {init_path}")
    
    return created

def main():
    """
    Main entry point to setup the project directory structure.
    """
    print("Setting up project directories...")
    dirs = create_directories()
    inits = create_init_files()
    print(f"Setup complete. Created {len(dirs)} directories and {len(inits)} init files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())