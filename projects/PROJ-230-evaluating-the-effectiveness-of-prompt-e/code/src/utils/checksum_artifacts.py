import os
import hashlib
import json
from pathlib import Path
from datetime import datetime

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory(directory_path: Path) -> list:
    """Scan a directory recursively and return list of file paths."""
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
    
    files = []
    for root, _, filenames in os.walk(directory_path):
        for filename in filenames:
            file_path = Path(root) / filename
            # Skip hidden files and common cache files
            if filename.startswith('.') or filename.endswith('.pyc'):
                continue
            files.append(file_path)
    return sorted(files)

def write_checksums(checksums: list, output_path: Path) -> None:
    """Write checksums to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "checksums": checksums
    }
    with open(output_path, "w") as f:
        json.dump(checksum_data, f, indent=2)

def main():
    """Main function to generate checksums for data/raw/ files."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    state_checksums_dir = project_root / "state" / "checksums"
    
    if not data_raw_dir.exists():
        print(f"Warning: {data_raw_dir} does not exist. Creating empty checksum file.")
        state_checksums_dir.mkdir(parents=True, exist_ok=True)
        empty_checksum_path = state_checksums_dir / "raw_checksums.json"
        write_checksums([], empty_checksum_path)
        print(f"Created empty checksum file at {empty_checksum_path}")
        return
    
    files = scan_directory(data_raw_dir)
    checksums = []
    
    for file_path in files:
        try:
            file_hash = compute_sha256(file_path)
            checksums.append({
                "file_path": str(file_path.relative_to(project_root)),
                "sha256": file_hash,
                "size_bytes": file_path.stat().st_size
            })
            print(f"Hashed: {file_path.relative_to(project_root)} -> {file_hash[:16]}...")
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
    
    output_path = state_checksums_dir / "raw_checksums.json"
    write_checksums(checksums, output_path)
    print(f"Checksums written to {output_path}")
    print(f"Total files processed: {len(checksums)}")

if __name__ == "__main__":
    main()
