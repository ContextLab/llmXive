"""
Checksum Recorder for FR-007 Compliance

Records SHA-256 checksums for all data files in data/ directory
and generates documentation in docs/reproducibility/checksums.md

Per Constitution Principle V: Content hashes recorded for reproducibility verification
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs" / "reproducibility"

@dataclass
class ChecksumEntry:
    """Represents a single file checksum entry."""
    file_path: str
    algorithm: str
    hash_value: str
    file_size_bytes: int
    recorded_at: str

@dataclass
class ChecksumRecord:
    """Complete checksum record for all data files."""
    checksums: List[ChecksumEntry]
    recorded_at: str
    total_files: int
    data_directory: str

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def find_data_files(data_dir: Path) -> List[Path]:
    """
    Find all data files in data/ directory and subdirectories.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        List of file paths
    """
    data_files = []
    for pattern in ["**/*.json", "**/*.csv", "**/*.txt", "**/*.md", "**/*.png"]:
        data_files.extend(data_dir.glob(pattern))
    # Filter out checksums files to avoid circular references
    return [f for f in data_files if "checksums" not in f.name.lower()]

def record_checksums(data_dir: Path = DATA_DIR) -> ChecksumRecord:
    """
    Compute and record checksums for all data files.
    
    Args:
        data_dir: Path to data directory (default: PROJECT_ROOT/data)
        
    Returns:
        ChecksumRecord with all checksum entries
    """
    data_files = find_data_files(data_dir)
    checksums = []
    recorded_at = datetime.utcnow().isoformat() + "Z"
    
    for file_path in sorted(data_files):
        rel_path = str(file_path.relative_to(data_dir))
        checksum_entry = ChecksumEntry(
            file_path=rel_path,
            algorithm="SHA-256",
            hash_value=compute_sha256(file_path),
            file_size_bytes=get_file_size(file_path),
            recorded_at=recorded_at
        )
        checksums.append(checksum_entry)
    
    return ChecksumRecord(
        checksums=checksums,
        recorded_at=recorded_at,
        total_files=len(checksums),
        data_directory=str(data_dir)
    )

def write_checksums_file(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write checksums to a file in standard sha256sum format.
    
    Args:
        record: ChecksumRecord to write
        output_path: Path to output file
    """
    with open(output_path, "w") as f:
        f.write(f"# SHA-256 Checksums for Data Files\n")
        f.write(f"# Generated: {record.recorded_at}\n")
        f.write(f"# Total files: {record.total_files}\n")
        f.write(f"# Data directory: {record.data_directory}\n")
        f.write("#\n")
        f.write("# Format: <hash>  <file_path>\n")
        f.write("#\n\n")
        
        for entry in record.checksums:
            f.write(f"{entry.hash_value}  {entry.file_path}\n")

def write_checksums_json(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write checksums to a JSON file for programmatic access.
    
    Args:
        record: ChecksumRecord to write
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(asdict(record), f, indent=2)

def write_checksums_documentation(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write checksums documentation in Markdown format.
    
    Per FR-007: Document checksums for reproducibility verification.
    
    Args:
        record: ChecksumRecord to document
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc_content = f"""# Data File Checksums

## Overview

This document records SHA-256 checksums for all data files in the project to ensure
data integrity and reproducibility as required by FR-007.

## Recording Details

- **Recorded at**: {record.recorded_at}
- **Data directory**: `{record.data_directory}`
- **Total files checksummed**: {record.total_files}
- **Algorithm**: SHA-256

## Checksum Entries

| File Path | SHA-256 Hash | Size (bytes) |
|-----------|--------------|--------------|
"""
    for entry in record.checksums:
        doc_content += f"| {entry.file_path} | `{entry.hash_value}` | {entry.file_size_bytes:,} |\n"
    
    doc_content += f"""
## Verification

To verify data integrity, run:

```bash
# Navigate to data directory
cd data

# Verify checksums using sha256sum
sha256sum -c checksums.sha256

# Expected output: All files should show "OK"
```

## Purpose

These checksums serve multiple purposes:

1. **Data Integrity**: Detect any corruption or modification of data files
2. **Reproducibility**: Ensure exact same data is used across different runs
3. **Audit Trail**: Provide verifiable proof of data provenance
4. **Version Control**: Track when data files are modified

## Related Artifacts

- `data/checksums.sha256` - Machine-readable checksum file
- `data/checksums.json` - JSON format checksum record
- `docs/reproducibility/operation_logs.md` - Operation execution logs
- `docs/reproducibility/random_seeds.md` - Random seed documentation

## Compliance

This documentation satisfies FR-007 requirement for checksum generation and
documentation for all data files in the project.
"""
    
    with open(output_path, "w") as f:
        f.write(doc_content)

def main() -> int:
    """
    Main entry point for checksum recording.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Starting checksum recording...")
    
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Record checksums
    print(f"Scanning data directory: {DATA_DIR}")
    record = record_checksums(DATA_DIR)
    
    if record.total_files == 0:
        print("Warning: No data files found to checksum")
        return 0
    
    print(f"Found {record.total_files} data files")
    
    # Write checksum files
    checksums_sha256_path = DATA_DIR / "checksums.sha256"
    checksums_json_path = DATA_DIR / "checksums.json"
    checksums_md_path = DOCS_DIR / "checksums.md"
    
    print(f"Writing checksums to: {checksums_sha256_path}")
    write_checksums_file(record, checksums_sha256_path)
    
    print(f"Writing JSON record to: {checksums_json_path}")
    write_checksums_json(record, checksums_json_path)
    
    print(f"Writing documentation to: {checksums_md_path}")
    write_checksums_documentation(record, checksums_md_path)
    
    print("Checksum recording complete!")
    print(f"  - {checksums_sha256_path}")
    print(f"  - {checksums_json_path}")
    print(f"  - {checksums_md_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())