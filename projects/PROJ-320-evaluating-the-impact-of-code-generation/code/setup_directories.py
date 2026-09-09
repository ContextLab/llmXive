import os
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure for the llmXive pipeline.
    This ensures all necessary folders exist before data processing begins.
    """
    base_path = Path(".")
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "code/data",
        "code/analysis",
        "code/audit",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports/figures"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nTotal directories created: {created_count}")
    return created_count

def main():
    """Entry point for the directory setup script."""
    create_directories()

if __name__ == "__main__":
    main()
