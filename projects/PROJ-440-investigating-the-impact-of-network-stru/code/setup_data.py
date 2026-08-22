import os
import sys
import json
from pathlib import Path
from code.utils.checksums import setup_data_directories, generate_checksum_file

def main():
    """
    Main function to set up data directories and generate checksums.
    """
    base_path = Path(__file__).resolve().parent.parent
    data_dir = base_path / "data"
    
    # Create directories
    setup_data_directories(str(data_dir))
    
    # Generate checksum file
    checksum_file = data_dir / "checksums.json"
    generate_checksum_file(str(data_dir), str(checksum_file))

if __name__ == "__main__":
    main()