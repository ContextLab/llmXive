"""
Script to regenerate checksums for the data directory.
Usage: python code/utils/generate_checksums.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.checksums import generate_checksum_manifest

def main():
    """Generate checksum manifest for all data files."""
    data_dir = project_root / "data"
    manifest_path = data_dir / "checksums.json"
    
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        print("Run 'python code/utils/initialize_data.py' first to create the structure.")
        return 1
    
    print(f"Generating checksum manifest for: {data_dir}")
    print("-" * 50)
    
    checksums = generate_checksum_manifest(data_dir, manifest_path)
    
    file_count = len(checksums)
    if file_count == 0:
        print("No files found to checksum.")
    else:
        print(f"Checksums generated for {file_count} files.")
        print(f"Manifest saved to: {manifest_path}")
    
    print("-" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())