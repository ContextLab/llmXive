import os
import sys
import logging
from pathlib import Path
from config import CONFIG
from utils.checksums import generate_all_checksums

def main():
    """
    Generate SHA-256 checksums for all raw and intermediate files
    and write them to data/provenance/checksums.txt
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting checksum generation for provenance tracking")

    # Define directories to scan for checksums
    directories_to_scan = [
        CONFIG.DATA_RAW_DIR,
        CONFIG.DATA_INTERMEDIATE_DIR,
        CONFIG.DATA_PROCESSED_DIR,
    ]

    # Filter to existing directories only
    valid_dirs = [d for d in directories_to_scan if d.exists()]
    
    if not valid_dirs:
        logger.warning("No data directories found to generate checksums for")
        # Still create the output file even if empty, to maintain provenance record
        checksums_path = CONFIG.DATA_PROVENANCE_DIR / "checksums.txt"
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        checksums_path.write_text("# No data files found to checksum\n")
        return

    logger.info(f"Scanning directories: {[str(d) for d in valid_dirs]}")

    # Generate checksums for all files in valid directories
    checksums = generate_all_checksums(valid_dirs)

    if not checksums:
        logger.warning("No files found to checksum in the specified directories")
        checksums_path = CONFIG.DATA_PROVENANCE_DIR / "checksums.txt"
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        checksums_path.write_text("# No files found to checksum\n")
        return

    # Write checksums to provenance file
    checksums_path = CONFIG.DATA_PROVENANCE_DIR / "checksums.txt"
    checksums_path.parent.mkdir(parents=True, exist_ok=True)

    with open(checksums_path, 'w') as f:
        f.write(f"# Checksums generated at {CONFIG.PROVENANCE_TIMESTAMP}\n")
        f.write(f"# Project: {CONFIG.PROJECT_ID}\n")
        f.write("# Format: <sha256_hash>  <relative_path>\n")
        f.write("#" + "=" * 78 + "\n")
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")

    logger.info(f"Successfully wrote {len(checksums)} checksums to {checksums_path}")
    
    # Log provenance event
    from utils.logging import log_provenance_event
    log_provenance_event(
        event_type="checksum_generation",
        details={
            "output_file": str(checksums_path),
            "files_checksummed": len(checksums),
            "directories_scanned": [str(d) for d in valid_dirs]
        }
    )

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
