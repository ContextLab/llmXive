import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

from config.env_config import get_processed_dir
from logging_config import setup_logging, get_logger
from aggregate_descriptors import load_processed_configs, save_aggregated_data

def main():
    """
    T027: Save processed descriptors to data/processed/descriptors.csv.
    
    This task aggregates the descriptors calculated in US2 (T022-T026) 
    and saves them to the canonical CSV location.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    processed_dir = get_processed_dir()
    input_file = processed_dir / "aggregated_descriptors.json"
    output_file = processed_dir / "descriptors.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. "
                     "Ensure T025 (Aggregate all descriptors) has run successfully.")
        raise FileNotFoundError(f"Required input file missing: {input_file}")
    
    logger.info(f"Loading aggregated descriptors from {input_file}")
    data = load_processed_configs(input_file)
    
    if not data:
        logger.warning("No data found in aggregated descriptors file.")
        # Create empty CSV with headers if no data, but log warning
        headers = ["config_id", "thermal_conductivity", "ring_3", "ring_4", "ring_5", 
                   "ring_6", "ring_7", "ring_8", "ring_9", "ring_10", 
                   "steinhardt_q6", "clustering_coefficient", "vdos_missing"]
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        logger.info(f"Created empty descriptors file at {output_file}")
        return
    
    logger.info(f"Saving {len(data)} configurations to {output_file}")
    save_aggregated_data(data, output_file)
    
    logger.info(f"Successfully saved descriptors to {output_file}")

if __name__ == "__main__":
    main()