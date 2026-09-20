"""
Sample Validator Module

Verifies the existence and validity of pre-equilibrated amorphous silicon samples
generated in data/raw/. Ensures exactly N=10 valid XYZ files exist before proceeding.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_valid_xyz_file(file_path: Path) -> bool:
    """
    Validates that a file is a properly formatted XYZ file with at least 1000 atoms.

    Args:
        file_path: Path to the XYZ file.

    Returns:
        True if valid, False otherwise.
    """
    if not file_path.exists():
        return False

    if not file_path.suffix.lower() == '.xyz':
        return False

    try:
        with open(file_path, 'r') as f:
            # First line: atom count
            first_line = f.readline().strip()
            if not first_line.isdigit():
                logger.warning(f"Invalid atom count line in {file_path}: {first_line}")
                return False

            atom_count = int(first_line)

            # Must have at least 1000 atoms as per task requirements
            if atom_count < 1000:
                logger.warning(f"File {file_path} has only {atom_count} atoms (< 1000).")
                return False

            # Check that comment line exists
            comment_line = f.readline()
            if not comment_line:
                logger.warning(f"Missing comment line in {file_path}")
                return False

            # Check that atom lines exist
            lines_read = 2
            for line in f:
                lines_read += 1
                if lines_read > atom_count + 2:
                    break

            if lines_read != atom_count + 2:
                logger.warning(f"Atom count mismatch in {file_path}: expected {atom_count} atoms, found {lines_read - 2}")
                return False

            return True

    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False


def scan_raw_directory(raw_dir: Path) -> List[Path]:
    """
    Scans the raw data directory for valid XYZ files.

    Args:
        raw_dir: Path to the data/raw directory.

    Returns:
        List of valid XYZ file paths.
    """
    if not raw_dir.exists():
        logger.error(f"Raw directory does not exist: {raw_dir}")
        return []

    valid_files = []
    for file_path in sorted(raw_dir.glob("*.xyz")):
        if is_valid_xyz_file(file_path):
            valid_files.append(file_path)
            logger.info(f"Valid sample found: {file_path.name} ({file_path.stat().st_size} bytes)")
        else:
            logger.warning(f"Invalid sample skipped: {file_path.name}")

    return valid_files


def write_sample_count(count: int, output_path: Path) -> None:
    """
    Writes the sample count verification result to a JSON file.

    Args:
        count: The number of valid samples found.
        output_path: Path to the output JSON file.
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "count": count,
        "expected": 10,
        "status": "VERIFIED" if count == 10 else "FAILED",
        "message": f"Found {count} valid samples. Expected 10." if count == 10 else f"ERROR: Found {count} valid samples. Expected 10. Pipeline halted."
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Sample count report written to {output_path}")


def main() -> int:
    """
    Main entry point for sample validation.

    Returns:
        0 if validation passes, 1 if it fails.
    """
    config = get_config()
    paths = get_paths()

    raw_dir = paths['raw_data']
    output_file = paths['processed_graphs'] / 'sample_count.json'

    logger.info(f"Scanning {raw_dir} for valid XYZ samples...")
    valid_samples = scan_raw_directory(raw_dir)

    count = len(valid_samples)
    logger.info(f"Found {count} valid samples.")

    write_sample_count(count, output_file)

    if count != 10:
        logger.error(f"VALIDATION FAILED: Expected 10 samples, found {count}.")
        logger.error("Pipeline halted. Please ensure T013a (sample generation) has completed successfully.")
        return 1

    logger.info("VALIDATION PASSED: Exactly 10 valid samples found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
