"""
Generate SHA-256 checksums for all raw and intermediate data artifacts.

This script implements Task T019:
- Scans data/raw/ and data/intermediate/ for data files (.csv, .json, .jsonl, .txt)
- Computes SHA-256 checksums using utils.checksums.generate_checksum
- Writes results to data/provenance/checksums.txt in standard format:
  <hash>  <relative_path>
- Logs provenance events for each file processed
"""
import os
import sys
import logging
from pathlib import Path

from config import CONFIG
from utils.checksums import generate_checksum
from utils.logging import get_logger, log_provenance_event

# Configure logger
logger = get_logger(__name__)

def generate_all_checksums():
    """
    Generate checksums for all data artifacts in data/raw/ and data/intermediate/.
    
    Returns:
        dict: Mapping of relative_path -> checksum
    """
    checksums = {}
    data_dirs = [
        CONFIG.DATA_RAW_DIR,
        CONFIG.DATA_INTERMEDIATE_DIR,
        CONFIG.DATA_PROVENANCE_DIR
    ]
    
    # Extensions to include
    valid_extensions = {'.csv', '.json', '.jsonl', '.txt', '.yaml', '.yml'}
    
    for data_dir in data_dirs:
        if not os.path.exists(data_dir):
            logger.warning(f"Directory does not exist, skipping: {data_dir}")
            continue
        
        dir_path = Path(data_dir)
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                # Skip the checksums file itself to avoid circular reference
                if file_path.name == 'checksums.txt':
                    continue
                
                try:
                    checksum = generate_checksum(file_path)
                    relative_path = file_path.relative_to(CONFIG.PROJECT_ROOT)
                    checksums[str(relative_path)] = checksum
                    logger.info(f"Generated checksum for: {relative_path}")
                    log_provenance_event(
                        event_type="checksum_generated",
                        artifact=str(relative_path),
                        checksum=checksum,
                        logger=logger
                    )
                except Exception as e:
                    logger.error(f"Failed to generate checksum for {file_path}: {e}")
                    raise
    
    return checksums

def write_checksums_file(checksums: dict, output_path: Path):
    """
    Write checksums to file in standard format:
    <hash>  <relative_path>
    
    Args:
        checksums: Mapping of relative_path -> checksum
        output_path: Path to write the checksums file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for relative_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {relative_path}\n")
    
    logger.info(f"Checksums written to: {output_path}")
    log_provenance_event(
        event_type="checksums_file_written",
        artifact=str(output_path.relative_to(CONFIG.PROJECT_ROOT)),
        file_count=len(checksums),
        logger=logger
    )

def main():
    """Main entry point for checksum generation."""
    logger.info("Starting checksum generation for data artifacts")
    
    try:
        # Generate checksums for all data files
        checksums = generate_all_checksums()
        
        if not checksums:
            logger.warning("No data files found to checksum. This may indicate missing data.")
            # Don't fail if no files exist - might be early in pipeline
            # But log it clearly for provenance
            log_provenance_event(
                event_type="no_data_files_found",
                message="No data files found in data/raw/ or data/intermediate/",
                logger=logger
            )
        
        # Write to provenance directory
        output_path = CONFIG.DATA_PROVENANCE_DIR / 'checksums.txt'
        write_checksums_file(checksums, output_path)
        
        logger.info(f"Checksum generation completed. Total files: {len(checksums)}")
        return 0
        
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
