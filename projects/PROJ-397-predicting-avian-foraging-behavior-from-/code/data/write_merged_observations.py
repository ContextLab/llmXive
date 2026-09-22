import os
import sys
import logging
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Import from project utils and existing modules
from utils.config import get_project_root, get_processed_dir, get_metadata_file
from utils.provenance import load_metadata_config, save_metadata_config, compute_file_hash, record_artifact_provenance

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define required columns for the merged observations dataset
REQUIRED_COLUMNS = {
    'species_id',
    'foraging_guild',
    'latitude',
    'longitude',
    'observation_date',
    'forest_prop_100m',
    'grassland_prop_100m',
    'wetland_prop_100m',
    'urban_prop_100m',
    'other_prop_100m'
}

def load_joined_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the joined data from the CSV file produced by join_guild_labels.py.
    
    Args:
        input_path: Path to the joined CSV file
        
    Returns:
        List of dictionaries representing the rows
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['latitude', 'longitude']:
                if key in row and row[key]:
                    row[key] = float(row[key])
            for key in ['forest_prop_100m', 'grassland_prop_100m', 'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m']:
                if key in row and row[key]:
                    row[key] = float(row[key])
            data.append(row)
    
    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data

def validate_schema(data: List[Dict[str, Any]], schema_path: Optional[Path] = None) -> None:
    """
    Validate that the data conforms to the expected schema.
    Raises ValueError if required columns are missing or data is malformed.
    
    Args:
        data: List of row dictionaries
        schema_path: Optional path to a YAML schema file (for future extensibility)
        
    Raises:
        ValueError: If schema validation fails
    """
    if not data:
        raise ValueError("Data is empty; cannot validate schema.")
    
    # Check that all required columns are present in the first row
    first_row_keys = set(data[0].keys())
    missing_columns = REQUIRED_COLUMNS - first_row_keys
    
    if missing_columns:
        raise ValueError(f"Missing required columns in dataset: {missing_columns}")
    
    # Validate data types and ranges for the first few rows
    for i, row in enumerate(data[:100]):  # Sample check for performance
        # Check numeric ranges for proportions
        prop_cols = ['forest_prop_100m', 'grassland_prop_100m', 'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m']
        total_prop = 0.0
        for col in prop_cols:
            val = row.get(col)
            if val is None:
                raise ValueError(f"Row {i}: Missing value for {col}")
            try:
                f_val = float(val)
                if not (0.0 <= f_val <= 1.0):
                    raise ValueError(f"Row {i}: {col} value {f_val} out of range [0, 1]")
                total_prop += f_val
            except (ValueError, TypeError) as e:
                raise ValueError(f"Row {i}: Invalid value for {col}: {val}") from e
        
        # Allow small floating point error in sum
        if abs(total_prop - 1.0) > 0.01:
            logger.warning(f"Row {i}: Land cover proportions sum to {total_prop:.4f} (expected ~1.0)")
        
        # Validate coordinates
        lat = row.get('latitude')
        lon = row.get('longitude')
        if lat is None or lon is None:
            raise ValueError(f"Row {i}: Missing coordinates")
        if not (-90 <= float(lat) <= 90):
            raise ValueError(f"Row {i}: Latitude {lat} out of range [-90, 90]")
        if not (-180 <= float(lon) <= 180):
            raise ValueError(f"Row {i}: Longitude {lon} out of range [-180, 180]")
        
        # Validate species_id and foraging_guild are non-empty strings
        if not row.get('species_id') or not isinstance(row['species_id'], str):
            raise ValueError(f"Row {i}: Invalid or missing species_id")
        if not row.get('foraging_guild') or not isinstance(row['foraging_guild'], str):
            raise ValueError(f"Row {i}: Invalid or missing foraging_guild")

def write_merged_observations(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the validated data to the output CSV file.
    
    Args:
        data: List of row dictionaries
        output_path: Path to the output CSV file
    """
    if not data:
        raise ValueError("Cannot write empty data to output file.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} records to {output_path}")

def record_provenance(output_path: Path, input_paths: List[Path]) -> None:
    """
    Record provenance information in metadata.yaml.
    
    Args:
        output_path: Path to the output file
        input_paths: List of input file paths
    """
    metadata = load_metadata_config()
    
    artifact_name = "merged_observations"
    record = {
        "artifact": artifact_name,
        "file": str(output_path.relative_to(get_project_root())),
        "sha256": compute_file_hash(output_path),
        "generated_at": datetime.utcnow().isoformat(),
        "input_files": [str(p.relative_to(get_project_root())) for p in input_paths],
        "description": "Merged observations with land cover proportions and foraging guild labels"
    }
    
    # Add to provenance records
    if "provenance" not in metadata:
        metadata["provenance"] = []
    
    # Remove existing record for this artifact if present
    metadata["provenance"] = [r for r in metadata["provenance"] if r.get("artifact") != artifact_name]
    metadata["provenance"].append(record)
    
    save_metadata_config(metadata)
    logger.info(f"Recorded provenance for {artifact_name} in metadata.yaml")

def main():
    """
    Main entry point for the script.
    Reads joined data, validates schema, writes merged observations, and records provenance.
    """
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    
    # Define input and output paths
    input_file = processed_dir / "joined_observations.csv"
    output_file = processed_dir / "merged_observations.csv"
    
    logger.info(f"Starting write_merged_observations process")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    try:
        # Load data
        logger.info("Loading joined data...")
        data = load_joined_data(input_file)
        
        # Validate schema
        logger.info("Validating schema...")
        validate_schema(data)
        logger.info("Schema validation passed.")
        
        # Write output
        logger.info("Writing merged observations...")
        write_merged_observations(data, output_file)
        
        # Record provenance
        logger.info("Recording provenance...")
        record_provenance(output_file, [input_file])
        
        logger.info("Successfully completed write_merged_observations.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()