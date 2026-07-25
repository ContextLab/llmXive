import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required data directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - data/splits
    - results
    
    Also creates .gitkeep files in each directory to ensure they are tracked
    by version control even when empty.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the directory structure relative to project root
    # Assuming the script is run from the project root or code/ directory
    # We'll determine the project root by looking for the parent of 'data'
    
    current_file = Path(__file__).resolve()
    # Try to find the project root by going up until we find 'data' or 'specs'
    project_root = current_file.parent
    while project_root != project_root.parent:
        if (project_root / 'data').exists() or (project_root / 'specs').exists():
            break
        project_root = project_root.parent
    
    # Define directories to create
    directories = [
        'data/raw',
        'data/processed',
        'data/splits',
        'results'
    ]
    
    success = True
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {full_path}")
            
            # Create .gitkeep file to ensure directory is tracked by git
            gitkeep_path = full_path / '.gitkeep'
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                print(f"  → Created .gitkeep in {full_path}")
            
        except Exception as e:
            print(f"✗ Failed to create directory {full_path}: {e}")
            success = False
    
    if success:
        print("\n✓ All required directories created successfully.")
        print(f"  Base path: {project_root}")
    else:
        print("\n✗ Some directories failed to create. Check errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
