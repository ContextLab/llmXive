import os
import sys
import logging
from pathlib import Path

from config import CONFIG
from utils.checksums import generate_all_checksums
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def main():
    """
    Generate checksums for all raw and intermediate files and save to
    data/provenance/checksums.txt.

    This task fulfills T019: Generate `data/provenance/checksums.txt`
    for all raw and intermediate files.
    """
    logger.info("Starting checksum generation for T019...")

    # Ensure the provenance directory exists
    provenance_dir = Path(CONFIG.PROVENANCE_DIR)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    # Define the files to checksum based on the pipeline outputs
    # We scan the raw and intermediate directories for CSV/JSONL files
    raw_dir = Path(CONFIG.RAW_DATA_DIR)
    intermediate_dir = Path(CONFIG.INTERMEDIATE_DATA_DIR)

    files_to_checksum = []

    if raw_dir.exists():
        for ext in ["*.csv", "*.jsonl", "*.json", "*.txt"]:
            files_to_checksum.extend(raw_dir.glob(ext))

    if intermediate_dir.exists():
        for ext in ["*.csv", "*.jsonl", "*.json", "*.txt"]:
            files_to_checksum.extend(intermediate_dir.glob(ext))

    if not files_to_checksum:
        logger.warning("No raw or intermediate files found to checksum.")
        # Still create an empty or minimal checksum file to indicate completion
        # but log the issue.
        checksum_file = provenance_dir / "checksums.txt"
        with open(checksum_file, "w") as f:
            f.write("# No data files found to checksum.\n")
        log_provenance_event("checksums_generated", status="empty", path=str(checksum_file))
        return

    logger.info(f"Found {len(files_to_checksum)} files to checksum.")

    # Generate checksums
    checksums = generate_all_checksums(files_to_checksum)

    # Write to the specific output file required by T019
    output_path = provenance_dir / "checksums.txt"
    with open(output_path, "w") as f:
        for filepath, checksum in checksums.items():
            # Format: <checksum>  <relative_path>
            f.write(f"{checksum}  {filepath}\n")

    logger.info(f"Checksums written to {output_path}")
    log_provenance_event("checksums_generated", status="success", path=str(output_path), count=len(checksums))

    print(f"Successfully generated checksums for {len(checksums)} files at {output_path}")

if __name__ == "__main__":
    main()
