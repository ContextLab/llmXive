import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.utils.checksums import update_checksum_for_file, save_checksums, load_checksums

logger = logging.getLogger(__name__)

class DataWriteError(Exception):
    pass

def write_dataset(data: List[Dict[str, Any]], filepath: str) -> None:
    """Write dataset to a JSON file."""
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Wrote {len(data)} items to {filepath}")
    except Exception as e:
        logger.error(f"Failed to write dataset to {filepath}: {e}")
        raise DataWriteError(f"Failed to write dataset: {e}")

def register_checksum(file_path: str, checksum_file: str) -> None:
    """Update the checksum for a specific file."""
    try:
        update_checksum_for_file(file_path, checksum_file)
        logger.info(f"Registered checksum for {file_path}")
    except Exception as e:
        logger.error(f"Failed to register checksum for {file_path}: {e}")
        raise DataWriteError(f"Checksum registration failed: {e}")

def generate_and_save_training_data(proofs: List[Dict], grids: List[Dict], output_dir: str) -> None:
    """Helper to save training data components."""
    proofs_path = os.path.join(output_dir, 'generated_proofs.json')
    grids_path = os.path.join(output_dir, 'generated_grids.json')
    write_dataset(proofs, proofs_path)
    write_dataset(grids, grids_path)

def main(args):
    """
    Main entry point for data writing task.
    Expects args.files (list of paths) and args.checksum_file.
    """
    if not hasattr(args, 'files') or not hasattr(args, 'checksum_file'):
        logger.error("Invalid arguments for data_writer main.")
        sys.exit(1)

    checksum_file = args.checksum_file
    # Ensure checksum file exists
    if not os.path.exists(checksum_file):
        save_checksums({}, checksum_file)

    for file_path in args.files:
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist, skipping checksum.")
            continue
        register_checksum(file_path, checksum_file)

    logger.info("Data writing and checksum registration complete.")
