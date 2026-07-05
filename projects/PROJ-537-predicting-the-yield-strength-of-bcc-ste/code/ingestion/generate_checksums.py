import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from utils.checksums import generate_all_checksums
from utils.logging import get_logger, log_provenance_event

def main():
    logger = get_logger(__name__)
    logger.info("Starting checksum generation for data provenance")

    # Define directories to scan for checksums
    # Based on T001 and T017, we need checksums for raw and intermediate files
    data_dirs = [
        CONFIG.DATA_RAW_DIR,
        CONFIG.DATA_INTERMEDIATE_DIR,
    ]

    all_checksums = {}

    for data_dir in data_dirs:
        dir_path = Path(data_dir)
        if not dir_path.exists():
            logger.warning(f"Directory {data_dir} does not exist, skipping")
            continue

        logger.info(f"Scanning directory: {dir_path}")
        dir_checksums = generate_all_checksums(dir_path)
        all_checksums.update(dir_checksums)

    if not all_checksums:
        logger.warning("No files found to checksum in data directories")
        return

    # Write checksums to the provenance file
    checksum_file = Path(CONFIG.DATA_PROVENANCE_DIR) / "checksums.txt"
    checksum_file.parent.mkdir(parents=True, exist_ok=True)

    with open(checksum_file, 'w') as f:
        for filepath, checksum in sorted(all_checksums.items()):
            f.write(f"{checksum}  {filepath}\n")

    logger.info(f"Generated checksums for {len(all_checksums)} files")
    logger.info(f"Checksums written to: {checksum_file}")

    # Log provenance event
    log_provenance_event(
        event_type="checksum_generation",
        artifact_path=str(checksum_file),
        details={
            "files_checksummed": len(all_checksums),
            "source_directories": [str(d) for d in data_dirs if Path(d).exists()]
        }
    )

    print(f"Successfully generated {checksum_file}")

if __name__ == "__main__":
    main()