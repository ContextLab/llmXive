"""
Task T013b: Verify sample count and validity for N=10.

Scans data/raw/ for valid XYZ files, asserts exactly 10 exist,
and writes the count to data/processed/graphs/sample_count.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Import existing utilities from the project
from config import get_config, get_paths

logger = logging.getLogger(__name__)

def is_valid_xyz_file(file_path: Path) -> bool:
    """
    Basic validation for an XYZ file.
    Returns True if the file exists, is readable, and has at least 2 lines
    (header + at least one atom).
    """
    if not file_path.is_file():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return False
            
            # First line should be the atom count (integer)
            try:
                atom_count = int(lines[0].strip())
                if atom_count < 1:
                    return False
                # Check if we have enough lines for header + atoms
                if len(lines) < atom_count + 2:
                    return False
            except ValueError:
                return False
            
            return True
    except (IOError, UnicodeDecodeError):
        return False

def scan_raw_directory(raw_dir: Path) -> List[Path]:
    """
    Scan the raw directory for valid XYZ files.
    Returns a list of valid file paths.
    """
    if not raw_dir.exists():
        logger.error(f"Raw directory does not exist: {raw_dir}")
        return []
    
    valid_files = []
    for file_path in raw_dir.iterdir():
        if file_path.suffix.lower() == '.xyz' and is_valid_xyz_file(file_path):
            valid_files.append(file_path)
    
    return sorted(valid_files)

def write_sample_count(count: int, output_path: Path) -> None:
    """
    Write the sample count to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"count": count}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Written sample count to {output_path}: {data}")

def main() -> int:
    """
    Main entry point for T013b.
    Returns 0 on success, 1 on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        config = get_config()
        paths = get_paths()
        
        raw_dir = paths.get('raw_data_dir', 'data/raw')
        raw_path = Path(raw_dir)
        
        output_path = paths.get('sample_count_file', 'data/processed/graphs/sample_count.json')
        output_file = Path(output_path)

        logger.info(f"Scanning raw directory: {raw_path}")
        valid_files = scan_raw_directory(raw_path)
        count = len(valid_files)

        logger.info(f"Found {count} valid XYZ files.")

        if count != 10:
            logger.error(f"VALIDATION FAILED: Expected exactly 10 valid XYZ files, but found {count}.")
            logger.error("Halt: Sample generation (T013a) may have failed or produced incorrect count.")
            # Write the actual count for debugging, but exit with error
            write_sample_count(count, output_file)
            return 1

        logger.info("Validation successful: Exactly 10 valid XYZ files found.")
        write_sample_count(count, output_file)
        return 0

    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
