import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksums import update_checksum_for_file, load_checksums, save_checksums

logger = logging.getLogger(__name__)

class DataWriteError(Exception):
    """Custom exception for data writing failures."""
    pass

def write_dataset(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes a list of dictionaries to a JSON file.
    
    Args:
        data: List of data records to write.
        output_path: Path to the output JSON file.
        
    Raises:
        DataWriteError: If writing fails.
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully wrote {len(data)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write dataset to {output_path}: {e}")
        raise DataWriteError(f"Failed to write dataset: {e}")

def register_checksum(file_path: str, checksums_path: str = "data/checksums.json") -> None:
    """
    Computes the checksum for a file and updates the central checksum registry.
    
    Args:
        file_path: Path to the file to checksum.
        checksums_path: Path to the checksums.json file.
    """
    try:
        update_checksum_for_file(file_path, checksums_path)
        logger.info(f"Checksum registered for {file_path}")
    except Exception as e:
        logger.error(f"Failed to register checksum for {file_path}: {e}")
        raise DataWriteError(f"Failed to register checksum: {e}")

def generate_and_save_training_data(
    proofs: List[Dict[str, Any]], 
    grids: List[Dict[str, Any]],
    data_dir: str = "data"
) -> None:
    """
    Orchestrates the saving of generated training data and checksum registration.
    
    Args:
        proofs: List of generated logic proof instances.
        grids: List of generated grid world instances.
        data_dir: Directory to save data files.
    """
    if not proofs and not grids:
        logger.warning("No data provided to save.")
        return

    Path(data_dir).mkdir(parents=True, exist_ok=True)
    checksums_file = os.path.join(data_dir, "checksums.json")

    # Save Proofs
    proofs_path = os.path.join(data_dir, "generated_proofs.json")
    if proofs:
        write_dataset(proofs, proofs_path)
        register_checksum(proofs_path, checksums_file)
    else:
        logger.warning("No proofs to save.")

    # Save Grids
    grids_path = os.path.join(data_dir, "generated_grids.json")
    if grids:
        write_dataset(grids, grids_path)
        register_checksum(grids_path, checksums_file)
    else:
        logger.warning("No grids to save.")

def main():
    """
    Entry point for the data writer script.
    Expects to be called by the generator pipeline or CLI.
    For standalone testing, it generates dummy data if no arguments are passed,
    but in the real pipeline, data is passed from upstream generators.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # If called directly without arguments, this is a dry-run or test mode.
    # In the real pipeline, this function is imported and called with real data.
    if len(sys.argv) > 1:
        # Expected usage: python -m src.generators.data_writer --proofs <path> --grids <path>
        # For now, we assume the CLI or generator calls this function directly.
        print("Data writer module loaded. Use generate_and_save_training_data() to save data.")
    else:
        print("Data writer module loaded. Use generate_and_save_training_data() to save data.")

if __name__ == "__main__":
    main()
