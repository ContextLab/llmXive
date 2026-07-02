import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the root project structure including code/, data/, tests/.
    This ensures the foundational layout exists before specific subdirectories are created.
    """
    # Determine the root directory (parent of this script's directory)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Core directories required by T001a
    core_dirs = ["code", "data", "tests"]
    
    created_count = 0
    
    for dirname in core_dirs:
        target_path = base_dir / dirname
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")
    
    # Create placeholder .gitkeep files for empty directories
    for dirname in core_dirs:
        target_path = base_dir / dirname / ".gitkeep"
        target_path.touch()
        
    return created_count

def main():
    """Entry point for script execution."""
    print("Initializing project root structure...")
    count = create_directories()
    print(f"Successfully created/verified {count} core directories.")
    print("Project root structure setup complete.")

if __name__ == "__main__":
    main()