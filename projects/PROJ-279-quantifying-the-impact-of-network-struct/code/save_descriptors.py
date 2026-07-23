import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

from config.env_config import get_processed_dir
from logging_config import setup_logging, get_logger
from state_manager import compute_file_checksum, register_artifact, save_state

logger = get_logger(__name__)

def load_processed_configs() -> List[Dict[str, Any]]:
    """
    Loads the aggregated descriptors from the intermediate JSON file produced by aggregate_descriptors.py.
    This file is expected to be at data/processed/descriptors_aggregated.json.
    """
    processed_dir = get_processed_dir()
    input_path = processed_dir / "descriptors_aggregated.json"
    
    if not input_path.exists():
        logger.error(f"Aggregated descriptors file not found at {input_path}. "
                     "Please run aggregate_descriptors.py first.")
        raise FileNotFoundError(f"Missing aggregated descriptors file: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def save_descriptors_to_csv(configs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the list of descriptor dictionaries to a CSV file.
    
    Args:
        configs: List of dictionaries where each dict represents a configuration 
                 with its ID, thermal conductivity, and topological/vibrational descriptors.
        output_path: Path object where the CSV file will be written.
    """
    if not configs:
        logger.warning("No configurations to save. CSV will be empty.")
        # Still create an empty file or a file with headers if we knew them
        # For now, we just write an empty file if list is empty
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    # Determine all possible keys from all configs to use as headers
    all_keys = set()
    for config in configs:
        all_keys.update(config.keys())
    
    # Ensure a consistent order: config_id, thermal_conductivity, then others
    headers = ['config_id', 'thermal_conductivity']
    remaining_keys = sorted([k for k in all_keys if k not in headers])
    headers.extend(remaining_keys)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(configs)

    logger.info(f"Successfully saved {len(configs)} configurations to {output_path}")

def main() -> None:
    """
    Main entry point for T027: Save processed descriptors to data/processed/descriptors.csv.
    
    1. Loads aggregated descriptors from data/processed/descriptors_aggregated.json.
    2. Saves them to data/processed/descriptors.csv.
    3. Registers the output file in the state manager.
    """
    setup_logging()
    logger.info("Starting T027: Saving processed descriptors to CSV.")
    
    processed_dir = get_processed_dir()
    output_path = processed_dir / "descriptors.csv"
    
    try:
        configs = load_processed_configs()
        save_descriptors_to_csv(configs, output_path)
        
        # Register artifact in state
        checksum = compute_file_checksum(output_path)
        register_artifact(
            path=output_path,
            task_id="T027",
            checksum=checksum,
            description="Processed descriptors CSV containing topological and vibrational metrics"
        )
        
        logger.info("T027 completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise
    except Exception as e:
        logger.exception(f"An error occurred during T027: {e}")
        raise

if __name__ == "__main__":
    main()
