import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    Creates: code/, data/, data/raw/, data/processed/, data/analysis/, tests/, contracts/, state/
    """
    base_dir = Path(".")
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

def main():
    setup_directories()

if __name__ == "__main__":
    main()
