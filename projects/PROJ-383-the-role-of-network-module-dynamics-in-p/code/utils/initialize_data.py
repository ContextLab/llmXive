import sys
from pathlib import Path
from utils.checksums import initialize_data_directories, generate_checksum_manifest, save_checksums, CHECKSUM_MANIFEST_FILE

def main():
    """
    Initialize the data directory structure and create the initial checksum manifest.
    This script is the primary entry point for setting up the data infrastructure.
    """
    print("Initializing data directory structure...")
    initialize_data_directories()
    
    print("Generating initial checksum manifest...")
    manifest = generate_checksum_manifest()
    save_checksums(manifest, CHECKSUM_MANIFEST_FILE)
    
    print(f"Data initialization complete.")
    print(f"Created directories: {', '.join([str(Path('data') / d) for d in ['raw_fmri', 'raw_behavior', 'processed', 'results']])}")
    print(f"Manifest saved to: {CHECKSUM_MANIFEST_FILE}")

if __name__ == "__main__":
    main()
