"""
Setup data directory structure and initialize checksums file.

This script creates the required directory hierarchy for raw and processed data
and initializes an empty checksums.txt file for data integrity tracking.
"""
import os
from pathlib import Path

def setup_data_structure(project_root: str) -> dict:
    """
    Create data directory structure and checksums file.

    Args:
        project_root: Path to the project root directory.

    Returns:
        Dictionary with status information about created paths.
    """
    base_path = Path(project_root)
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    checksums_file = data_root / "checksums.txt"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize checksums file if it doesn't exist
    if not checksums_file.exists():
        checksums_file.write_text(
          "# SHA-256 checksums for raw data files\n"
          "# Format: <hash>  <filename>\n"
          "# Generated: setup_data_structure.py\n"
        )

    return {
        "data_root": str(data_root),
        "raw_dir": str(raw_dir),
        "processed_dir": str(processed_dir),
        "checksums_file": str(checksums_file),
        "created": True
    }

if __name__ == "__main__":
    import sys
    # Default to current directory if no argument provided
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    result = setup_data_structure(project_root)
    print(f"Data structure setup complete:")
    print(f"  Data root: {result['data_root']}")
    print(f"  Raw directory: {result['raw_dir']}")
    print(f"  Processed directory: {result['processed_dir']}")
    print(f"  Checksums file: {result['checksums_file']}")