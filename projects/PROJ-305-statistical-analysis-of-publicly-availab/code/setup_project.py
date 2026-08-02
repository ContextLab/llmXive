import os
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as per the implementation plan.
    Directories: src/, tests/, data/, output/
    """
    base_dir = Path(__file__).parent.parent
    
    # Define the required directories
    directories = [
        base_dir / "src",
        base_dir / "tests",
        base_dir / "data",
        base_dir / "output"
    ]
    
    # Create subdirectories for organization
    subdirectories = [
        base_dir / "src" / "utils",
        base_dir / "src" / "data",
        base_dir / "src" / "analysis",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "output" / "temporal_profiles"
    ]
    
    all_dirs = directories + subdirectories
    
    created_count = 0
    for directory in all_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory.relative_to(base_dir)}")
        else:
            print(f"Directory already exists: {directory.relative_to(base_dir)}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return all_dirs

if __name__ == "__main__":
    create_directories()
