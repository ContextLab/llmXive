import os
from pathlib import Path

def main():
    """
    Creates the required test directory structure for the project.
    
    Directories created relative to the project root:
    - tests/unit/
    - tests/integration/
    - tests/contract/
    """
    # Define the project root (assuming this script is run from the project root)
    # or explicitly set the base path if needed.
    # Based on the task description, we are working within:
    # projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
    
    # We assume the script is executed from the project root directory.
    base_path = Path(".")
    
    test_base = base_path / "tests"
    
    directories = [
        test_base / "unit",
        test_base / "integration",
        test_base / "contract"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All required test directories already exist.")
    else:
        print(f"Successfully created {created_count} new test directories.")

if __name__ == "__main__":
    main()
