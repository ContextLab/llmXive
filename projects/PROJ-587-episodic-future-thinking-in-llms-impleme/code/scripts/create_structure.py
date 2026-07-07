import os
from pathlib import Path

def main():
    """
    Creates the standard project directory structure for PROJ-587.
    This ensures all required folders for data, models, services, and tests exist.
    """
    project_root = Path("projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code")
    
    # Define the directory structure relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "models",
        "services",
        "experiments",
        "validation",
        "utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "scripts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    main()