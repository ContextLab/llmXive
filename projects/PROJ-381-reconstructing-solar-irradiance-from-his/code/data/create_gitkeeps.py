import os
from pathlib import Path

def main():
    """
    Create .gitkeep files in data/raw/ and data/processed/ directories.
    This ensures these directories are tracked by git even when empty.
    """
    # Define the paths relative to the project root
    # We assume this script is run from the project root or the code directory
    # The paths are relative to the project root
    
    project_root = Path(__file__).parent.parent.parent
    data_raw_path = project_root / "data" / "raw"
    data_processed_path = project_root / "data" / "processed"
    
    directories_to_keep = [data_raw_path, data_processed_path]
    
    for directory in directories_to_keep:
        # Create the directory if it doesn't exist (defensive, though T001a should have done this)
        directory.mkdir(parents=True, exist_ok=True)
        
        gitkeep_file = directory / ".gitkeep"
        
        # Write the .gitkeep file
        # Content is just a comment explaining the file's purpose
        gitkeep_file.write_text("# This file ensures the directory is tracked by git\n")
        
        print(f"Created .gitkeep in: {gitkeep_file}")

if __name__ == "__main__":
    main()
