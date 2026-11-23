import os
import sys
import logging
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_processed_dir, get_metadata_file, get_file_path
from utils.provenance import compute_file_hash, record_artifact_provenance, load_metadata_config, save_metadata_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Required columns for the merged observations dataset
REQUIRED_COLUMNS = [
    'species_id', 'foraging_guild', 'latitude', 'longitude', 'observation_date',
    'forest_prop_100m', 'grassland_prop_100m', 'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m'
]

def load_joined_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the joined data from a CSV file.
    
    Args:
        input_path: Path to the input CSV file (output of join_guild_labels.py)
        
    Returns:
        List of dictionaries representing rows
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['latitude'] = float(row['latitude'])
                row['longitude'] = float(row['longitude'])
                row['forest_prop_100m'] = float(row['forest_prop_100m'])
                row['grassland_prop_100m'] = float(row['grassland_prop_100m'])
                row['wetland_prop_100m'] = float(row['wetland_prop_100m'])
                row['urban_prop_100m'] = float(row['urban_prop_100m'])
                row['other_prop_100m'] = float(row['other_prop_100m'])
            except ValueError as e:
                logger.warning(f"Skipping row due to conversion error: {e}")
                continue
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def validate_schema(data: List[Dict[str, Any]]) -> None:
    """
    Validate that the data conforms to the required schema.
    Raises ValueError if required columns are missing or data is malformed.
    
    Args:
        data: List of dictionaries to validate
        
    Raises:
        ValueError: If schema validation fails
    """
    if not data:
        raise ValueError("Data is empty; cannot validate schema.")
    
    # Check for required columns in the first row
    first_row_keys = set(data[0].keys())
    missing_columns = set(REQUIRED_COLUMNS) - first_row_keys
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validate data types and ranges for a sample of rows
    for i, row in enumerate(data):
        # Check latitude range
        if not (-90 <= row['latitude'] <= 90):
            raise ValueError(f"Invalid latitude at row {i}: {row['latitude']}")
        
        # Check longitude range
        if not (-180 <= row['longitude'] <= 180):
            raise ValueError(f"Invalid longitude at row {i}: {row['longitude']}")
        
        # Check that land cover proportions sum to ~1.0 (allowing for floating point errors)
        props = [
            row['forest_prop_100m'],
            row['grassland_prop_100m'],
            row['wetland_prop_100m'],
            row['urban_prop_100m'],
            row['other_prop_100m']
        ]
        prop_sum = sum(props)
        if not (0.99 <= prop_sum <= 1.01):
            raise ValueError(f"Land cover proportions do not sum to ~1.0 at row {i}: {prop_sum}")
        
        # Check for null guild
        if not row['foraging_guild'] or row['foraging_guild'].strip() == "":
            raise ValueError(f"Missing foraging_guild at row {i}")
    
    logger.info("Schema validation passed.")

def write_merged_observations(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the validated merged observations to a CSV file.
    
    Args:
        data: List of dictionaries to write
        output_path: Path for the output CSV file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    fieldnames = REQUIRED_COLUMNS
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Ensure only required columns are written
            filtered_row = {k: row[k] for k in fieldnames if k in row}
            writer.writerow(filtered_row)
    
    logger.info(f"Wrote {len(data)} rows to {output_path}")

def record_provenance(output_path: str) -> None:
    """
    Record provenance metadata for the output file.
    
    Args:
        output_path: Path to the generated CSV file
    """
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Cannot record provenance for missing file: {output_path}")
    
    file_hash = compute_file_hash(output_path)
    file_size = os.path.getsize(output_path)
    
    metadata = load_metadata_config()
    
    provenance_record = {
        "artifact_name": "merged_observations.csv",
        "source_file": output_path,
        "sha256_hash": file_hash,
        "file_size_bytes": file_size,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "write_merged_observations.py",
        "description": "Merged observations with land cover proportions and foraging guild labels",
        "input_artifacts": [
            "filtered_ebd.csv",
            "guild_mapping.csv",
            "nlcd_2019.zip"
        ]
    }
    
    if "artifacts" not in metadata:
        metadata["artifacts"] = {}
    
    metadata["artifacts"]["merged_observations.csv"] = provenance_record
    
    save_metadata_config(metadata)
    logger.info(f"Recorded provenance for {output_path} with hash {file_hash}")

def main():
    """Main entry point for the script."""
    # Define paths
    processed_dir = get_processed_dir()
    input_path = get_file_path(processed_dir, "joined_with_guilds.csv")
    output_path = get_file_path(processed_dir, "merged_observations.csv")
    
    logger.info(f"Starting write_merged_observations.py")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load data
    try:
        data = load_joined_data(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Validate schema
    try:
        validate_schema(data)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    
    # Write output
    try:
        write_merged_observations(data, output_path)
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        sys.exit(1)
    
    # Record provenance
    try:
        record_provenance(output_path)
    except Exception as e:
        logger.error(f"Failed to record provenance: {e}")
        sys.exit(1)
    
    logger.info("write_merged_observations.py completed successfully.")

if __name__ == "__main__":
    main()
