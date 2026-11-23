"""
T012a: Read Dataset IDs

Reads dataset IDs from data/dataset_ids.txt and outputs a list of IDs to be processed.
This script is the entry point for the data acquisition pipeline's ID resolution phase.

Logic:
1. Read IDs from data/dataset_ids.txt (pre-populated by T004a).
2. Parse the list of dataset IDs (ignoring comments and empty lines).
3. Output: A list of IDs to be processed (printed to stdout and returned).
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent.parent / "data"

def read_dataset_ids(ids_file_path: Path) -> list[str]:
    """
    Read dataset IDs from a file.

    Args:
        ids_file_path: Path to the dataset IDs file.

    Returns:
        List of dataset IDs (strings).

    Raises:
        FileNotFoundError: If the IDs file does not exist.
        ValueError: If the file is empty or contains no valid IDs.
    """
    if not ids_file_path.exists():
        raise FileNotFoundError(f"Dataset IDs file not found: {ids_file_path}")

    ids = []
    with open(ids_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Validate format: source:id
            if ':' not in line:
                logger.warning(f"Ignoring malformed line {line_num}: '{line}' (missing ':')")
                continue

            source, dataset_id = line.split(':', 1)
            source = source.strip()
            dataset_id = dataset_id.strip()

            if not source or not dataset_id:
                logger.warning(f"Ignoring malformed line {line_num}: '{line}' (empty source or id)")
                continue

            full_id = f"{source}:{dataset_id}"
            ids.append(full_id)
            logger.info(f"Found dataset ID: {full_id}")

    if not ids:
        raise ValueError("No valid dataset IDs found in the file.")

    return ids

def main():
    """Main entry point for T012a."""
    data_dir = get_data_dir()
    ids_file = data_dir / "dataset_ids.txt"

    logger.info(f"Reading dataset IDs from: {ids_file}")

    try:
        dataset_ids = read_dataset_ids(ids_file)
        logger.info(f"Successfully parsed {len(dataset_ids)} dataset IDs.")

        # Output the list to stdout for downstream piping or verification
        for ds_id in dataset_ids:
            print(ds_id)

        return dataset_ids

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()