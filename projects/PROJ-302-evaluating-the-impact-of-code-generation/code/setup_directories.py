import os
from pathlib import Path

def create_directories():
    """
    Create the required subdirectories for the project structure.
    Specifically creates:
    - code/data_acquisition/
    - code/feature_extraction/
    - code/analysis/
    - code/utils/
    
    These directories are required for organizing the pipeline modules.
    """
    base_path = Path(__file__).parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "code/data_acquisition",
        "code/feature_extraction",
        "code/analysis",
        "code/utils"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_dirs

def main():
    """Main entry point for directory creation."""
    print("Starting directory creation for T001d...")
    created = create_directories()
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("All required directories already exist.")
    print("T001d task complete.")

if __name__ == "__main__":
    main()