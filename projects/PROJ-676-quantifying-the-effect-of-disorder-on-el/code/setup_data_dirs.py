import os
import json
from pathlib import Path
from code.config import get_config

def main():
    """Main entry point for ensuring data directories exist."""
    config = get_config()
    
    # Ensure all data directories exist
    data_dirs = [
        config["DATA_RAW_PATH"],
        config["DATA_PROCESSED_PATH"],
        config["DATA_METADATA_PATH"],
        config["FIGURES_PATH"]
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")
    
    # Create a metadata file to confirm setup
    metadata_file = config["DATA_METADATA_PATH"] / "setup_timestamp.json"
    with open(metadata_file, 'w') as f:
        json.dump({
            "setup_complete": True,
            "timestamp": os.popen("date").read().strip()
        }, f, indent=2)
    
    print(f"Setup metadata written to {metadata_file}")
    return 0

if __name__ == "__main__":
    exit(main())
