import os
import sys
import json
from pathlib import Path

# Import the setup function from setup_directories
# Note: We assume this file is run from the project root or code/ directory
# Adjust import path if necessary
try:
    from code.setup_directories import setup_directories
    from code.utils.checksums import setup_data_directories, generate_checksum_file
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from code.setup_directories import setup_directories
    from code.utils.checksums import setup_data_directories, generate_checksum_file

def main():
    """
    Main entry point to initialize the project data structure.
    Calls setup_directories to create folders and setup_data_directories 
    to initialize checksum tracking if needed.
    """
    print("Initializing project data structure...")
    
    # 1. Create directory structure
    setup_directories()
    
    # 2. Initialize checksum infrastructure (creates state/checksums.json if missing)
    # This ensures the 'state/' directory is ready for artifact tracking
    setup_data_directories()
    
    print("Project data structure initialization complete.")

if __name__ == "__main__":
    main()