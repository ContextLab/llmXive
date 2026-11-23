import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_raw_data_files(directory: str = 'data/raw') -> List[str]:
    """Get all raw data files."""
    path = Path(directory)
    if not path.exists():
        return []
    return [str(f) for f in path.rglob('*') if f.is_file()]

def generate_checksums(files: List[str]) -> Dict[str, str]:
    """Generate checksums for files."""
    return {f: calculate_sha256(f) for f in files}

def write_checksum_log(checksums: Dict[str, str], log_path: str = 'artifacts/checksums.log') -> None:
    """Write checksums to log file."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"# Checksum Log - {datetime.now().isoformat()}\n")
        for file_path, checksum in checksums.items():
            f.write(f"{checksum}  {file_path}\n")

def main():
    """Generate checksums for raw data."""
    files = get_raw_data_files()
    if not files:
        print("No raw data files found.")
        return 0
    
    checksums = generate_checksums(files)
    write_checksum_log(checksums)
    
    print(f"Generated checksums for {len(files)} files")
    return 0

if __name__ == '__main__':
    sys.exit(main())
