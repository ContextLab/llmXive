import hashlib
import os
import sys
from pathlib import Path
from typing import Optional

# Import from local utils if available, otherwise assume standard layout
# For T001 structure, we assume code/ is in the path
try:
    from setup_data_structure import ensure_directory
except ImportError:
    # Fallback if running from root
    sys.path.insert(0, str(Path(__file__).parent))
    from setup_data_structure import ensure_directory

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_raw_data_files(data_dir: str) -> list:
    """Get list of all files in data/raw directory."""
    raw_dir = Path(data_dir) / "raw"
    if not raw_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(raw_dir):
        for filename in filenames:
            # Skip .gitkeep files as they are placeholders
            if not filename.endswith(".gitkeep"):
                files.append(os.path.join(root, filename))
    return files

def write_checksums(checksums: dict, output_path: str) -> None:
    """Write checksums to a text file in standard checksum format."""
    ensure_directory(os.path.dirname(output_path))
    with open(output_path, 'w', encoding='utf-8') as f:
        for file_path, checksum in checksums.items():
            f.write(f"{checksum}  {file_path}\n")

def verify_checksums(checksum_file: str, data_dir: str) -> bool:
    """Verify file checksums against recorded values."""
    if not os.path.exists(checksum_file):
        print(f"Checksum file not found: {checksum_file}")
        return False
    
    raw_files = get_raw_data_files(data_dir)
    if not raw_files:
        print("No raw data files found to verify.")
        return True
    
    # Read recorded checksums
    recorded = {}
    with open(checksum_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split("  ", 1)
            if len(parts) == 2:
                recorded[parts[1]] = parts[0]
    
    all_valid = True
    for file_path in raw_files:
        if file_path not in recorded:
            print(f"Warning: No checksum recorded for {file_path}")
            continue
        
        current_hash = compute_sha256(file_path)
        if current_hash != recorded[file_path]:
            print(f"FAILED: {file_path}")
            print(f"  Expected: {recorded[file_path]}")
            print(f"  Got:      {current_hash}")
            all_valid = False
        else:
            print(f"OK: {file_path}")
    
    return all_valid

def main():
    """Main entry point for checksum verification."""
    # Determine project root based on execution context
    # If running from code/, go up one level
    if Path.cwd().name == "code":
        project_root = Path.cwd().parent
    else:
        project_root = Path.cwd()
        
    data_dir = project_root / "data"
    checksum_file = project_root / "data" / "checksums.txt"
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        if verify_checksums(str(checksum_file), str(data_dir)):
            print("All checksums verified successfully.")
            sys.exit(0)
        else:
            print("Checksum verification failed.")
            sys.exit(1)
    
    # Compute checksums for all raw files
    raw_files = get_raw_data_files(str(data_dir))
    if not raw_files:
        print("No raw data files found. Run data ingestion first.")
        # If data ingestion hasn't run yet, we create an empty checksum file
        # to indicate the state, but warn the user.
        ensure_directory(str(checksum_file.parent))
        checksum_file.touch()
        print(f"Created empty checksum file at {checksum_file}")
        sys.exit(0)
    
    checksums = {}
    for file_path in raw_files:
        print(f"Computing hash for {file_path}...")
        checksums[file_path] = compute_sha256(file_path)
    
    write_checksums(checksums, str(checksum_file))
    print(f"Checksums written to {checksum_file}")
    print(f"Total files processed: {len(checksums)}")

if __name__ == "__main__":
    main()