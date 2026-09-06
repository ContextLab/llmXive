import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in the implementation plan.
    
    Directories created:
    - code/
    - tests/
    - data/
    - data/raw/
    - data/checkpoints/
    - data/results/
    - data/logs/
    - tests/unit/
    - tests/integration/
    - tests/contract/
    """
    base_path = Path(__file__).parent.parent
    
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created = []
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created

def verify_structure():
    """
    Verifies that all required directories exist.
    
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    base_path = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    missing = []
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing.append(str(dir_path))
    
    if missing:
        print(f"Missing directories: {missing}")
        return False
    
    print("All required directories exist.")
    return True

if __name__ == "__main__":
    print("Creating project structure...")
    create_directories()
    print("\nVerifying structure...")
    if verify_structure():
        print("\nProject structure verification successful.")
        sys.exit(0)
    else:
        print("\nProject structure verification failed.")
        sys.exit(1)
