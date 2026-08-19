import os
import sys
import json
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.checksums import setup_data_directories, generate_checksum_file

def main():
    """
    Main entry point to setup the data directory structure and generate initial checksums.
    """
    base_dir = "data"
    
    print(f"Setting up directory structure under '{base_dir}'...")
    directories = setup_data_directories(base_dir)
    
    for name, path in directories.items():
        print(f"  Created: {path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for path in directories.values():
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"  Created: {gitkeep}")
    
    # Prepare to generate checksums for the directory structure itself (empty initially)
    # We create a placeholder checksum file for the directories
    checksum_path = os.path.join(base_dir, "checksums.json")
    
    # Since directories are empty, we just record their existence
    # In a real scenario, this would be populated after data generation
    initial_checksums = {}
    for name, path in directories.items():
        # We can't checksum an empty directory easily without content, 
        # so we record the directory structure state
        initial_checksums[f"dir:{name}"] = "structure_created"
        
    with open(checksum_path, 'w') as f:
        json.dump(initial_checksums, f, indent=2)
        
    print(f"Initialized checksum file: {checksum_path}")
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()