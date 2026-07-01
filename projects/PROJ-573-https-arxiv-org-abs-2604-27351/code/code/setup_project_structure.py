"""
Script to create the project directory structure.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    base_dir = Path("code")
    
    directories = [
        "src",
        "src/benchmark",
        "src/benchmark/config",
        "src/benchmark/config/modalities",
        "src/data",
        "src/data/processed",
        "src/evaluation",
        "src/models",
        "src/research",
        "src/tasks",
        "src/utils",
        "src/validators",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data",
        "data/processed",
        "state",
        "contracts",
        "research",
        "figures",
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files():
    """Create __init__.py files in all Python package directories."""
    base_dir = Path("code")
    src_dir = base_dir / "src"
    tests_dir = base_dir / "tests"
    
    # Find all directories under src and tests
    for directory in src_dir.rglob("*"):
        if directory.is_dir():
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created __init__.py: {init_file}")
    
    for directory in tests_dir.rglob("*"):
        if directory.is_dir():
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created __init__.py: {init_file}")

def main():
    """Main function to set up project structure."""
    print("Setting up project directory structure...")
    create_directories()
    create_init_files()
    print("✓ Project structure created successfully")

if __name__ == "__main__":
    main()
