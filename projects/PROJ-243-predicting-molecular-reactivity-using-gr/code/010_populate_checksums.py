import os
import sys
import json
import hashlib
import logging
from typing import Dict, Any, Optional

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, get_logger

def setup_script_logging():
    """Configure logging for the populate checksums script."""
    return setup_logging("populate_checksums")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_files_exist(file_paths: Dict[str, str], logger: logging.Logger) -> bool:
    """Validate that all required files exist.
    
    Args:
        file_paths: Dictionary mapping logical names to file paths.
        logger: Logger instance.
        
    Returns:
        True if all files exist, False otherwise.
    """
    all_exist = True
    for name, path in file_paths.items():
        if not os.path.exists(path):
            logger.error(f"Required file missing: {name} -> {path}")
            all_exist = False
        else:
            logger.info(f"Found required file: {name} -> {path}")
    return all_exist

def populate_checksums(
    file_paths: Dict[str, str],
    checksums_path: str,
    source_info: Dict[str, Dict[str, str]],
    logger: logging.Logger
) -> Dict[str, Any]:
    """Compute SHA-256 hashes and populate the checksums JSON file.
    
    Args:
        file_paths: Dictionary mapping logical names to file paths.
        checksums_path: Path to the output checksums JSON file.
        source_info: Dictionary containing source URL and version info for each file.
        logger: Logger instance.
        
    Returns:
        The populated checksums dictionary.
        
    Raises:
        FileNotFoundError: If any required file is missing.
        IOError: If a file cannot be read or written.
    """
    if not validate_files_exist(file_paths, logger):
        raise FileNotFoundError(
            "One or more required files are missing. Cannot populate checksums."
        )

    checksums = {}
    
    for name, path in file_paths.items():
        logger.info(f"Calculating SHA-256 for {name} at {path}...")
        file_hash = calculate_sha256(path)
        
        entry = {
            "hash": file_hash,
            "file": os.path.basename(path),
            "path": path
        }
        
        # Add source information if available
        if name in source_info:
            entry.update(source_info[name])
        
        checksums[name] = entry
        logger.info(f"  Hash: {file_hash}")

    # Write to JSON file
    logger.info(f"Writing checksums to {checksums_path}...")
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    
    logger.info("Checksums populated successfully.")
    return checksums

def main():
    """Main entry point for populating checksums."""
    logger = setup_script_logging()
    logger.info("Starting checksum population process.")
    
    try:
        config = get_config()
        ensure_directories()
        
        # Define the files to hash based on T010g schema and task requirements
        # These are the RAW files that must exist after T010a and T010d
        raw_file_paths = {
            "reference_substructures": os.path.join(
                config["data_raw_dir"], "reference_substructures_raw.csv"
            ),
            "kinetic_dataset": os.path.join(
                config["data_raw_dir"], "kinetic_dataset_raw.csv"
            )
        }
        
        # Source information for reproducibility (matching T010g requirements)
        # Note: URLs are placeholders; in a real run, these should match the actual download sources
        source_info = {
            "reference_substructures": {
                "source_url": "https://nist.gov/chemistry/reaction-data",
                "version": "1.0.0",
                "description": "Curated static file of known reactive substructures from NIST"
            },
            "kinetic_dataset": {
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid",
                "version": "1.0.0",
                "description": "External kinetic dataset of experimental reaction rates from PubChem"
            }
        }
        
        checksums_path = os.path.join(
            config["data_raw_dir"], "checksums.json"
        )
        
        checksums = populate_checksums(
            file_paths=raw_file_paths,
            checksums_path=checksums_path,
            source_info=source_info,
            logger=logger
        )
        
        logger.info("Checksum population completed successfully.")
        print(f"Checksums written to {checksums_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except IOError as e:
        logger.error(f"I/O error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
