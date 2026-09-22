import os
import hashlib
from pathlib import Path

# Ensure these imports exist or are added to utils.py if missing
# Based on API surface, we assume standard library and existing project structure
from utils import setup_logging

def ensure_directory(path: Path) -> None:
    """Ensure the directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging = setup_logging()
        logging.info(f"Created directory: {path}")
    elif not path.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {path}")

def initialize_checksums_file(checksums_path: Path) -> None:
    """Initialize the checksums.txt file if it doesn't exist."""
    if not checksums_path.exists():
        checksums_path.write_text("# Data Checksums for PROJ-334\n# Format: SHA256  filename\n")
        logging = setup_logging()
        logging.info(f"Initialized checksums file: {checksums_path}")

def main() -> None:
    """Main entry point for T004: Setup data directory structure."""
    # Determine project root (assuming script is run from project root or code/ dir)
    # We assume the project root is the parent of the 'code' directory
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent if code_dir.name == 'code' else code_dir.parent.parent

    # Define paths relative to project root
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    checksums_file = data_root / "checksums.txt"

    # Ensure directories exist
    ensure_directory(data_root)
    ensure_directory(raw_dir)
    ensure_directory(processed_dir)

    # Initialize checksums file
    initialize_checksums_file(checksums_file)

    print(f"Data directory structure setup complete at: {data_root}")
    print(f"  - Raw data: {raw_dir}")
    print(f"  - Processed data: {processed_dir}")
    print(f"  - Checksums: {checksums_file}")

if __name__ == "__main__":
    main()
