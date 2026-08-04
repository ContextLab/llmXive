import os
from pathlib import Path

def create_project_structure():
    """
    Creates the full internal directory structure for the project
    under projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/.
    
    Structure:
    code/
      src/
        generation/
        filtering/
        training/
        evaluation/
        utils/
      tests/
        unit/
        integration/
      data/
        raw/
        curated/
        eval/
        validation/
    """
    base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    if not base_path.exists():
        print(f"Error: Base path {base_path} does not exist. Run create_directories.py first.")
        return False

    # Define all required directories
    directories = [
        # Source modules
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils",
        
        # Test modules
        "tests/unit",
        "tests/integration",
        
        # Data directories
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
    ]

    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        except OSError as e:
            print(f"Error creating {full_path}: {e}")

    print(f"Created {created_count} subdirectories under {base_path}")
    return True

if __name__ == "__main__":
    success = create_project_structure()
    if success:
        print("Project structure initialization complete.")
    else:
        print("Project structure initialization failed.")