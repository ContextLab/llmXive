import os
from pathlib import Path

def create_test_directories():
    """
    Creates the required test subdirectories:
    - tests/contract/
    - tests/integration/
    - tests/unit/
    
    Returns True if successful, False otherwise.
    """
    base_path = Path("tests")
    
    directories = [
        base_path / "contract",
        base_path / "integration",
        base_path / "unit"
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            gitkeep_path = directory / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            print(f"Created directory: {directory} with .gitkeep")
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = create_test_directories()
    if success:
        print("Test directory structure created successfully.")
        exit(0)
    else:
        print("Failed to create test directory structure.")
        exit(1)