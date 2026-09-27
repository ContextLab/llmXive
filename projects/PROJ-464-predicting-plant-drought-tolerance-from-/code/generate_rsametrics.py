"""
T015 Implementation: Generate and validate rsametrics.csv.

This script aggregates RSA metrics extracted by preprocess_images.py,
validates them against the schema, and writes the final CSV.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import json
import yaml
from datetime import datetime

# Project imports
from preprocess_images import process_directory
from config import ensure_directories, get_config_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path("contracts/rsametrics.schema.yaml")
INPUT_DIR = Path("data/raw/nppn_images")
OUTPUT_DIR = Path("data/derived")
OUTPUT_FILE = OUTPUT_DIR / "rsametrics.csv"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema for validation."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_row(row: Dict[str, Any]) -> bool:
    """
    Validate a single row of data against schema constraints.
    Returns True if valid, raises ValueError if invalid.
    """
    required_fields = ['species_id', 'depth', 'branching_density', 'surface_area']
    
    for field in required_fields:
        if field not in row:
            raise ValueError(f"Missing required field: {field}")
        
        if field == 'species_id':
            if not isinstance(row[field], str) or len(row[field]) == 0:
                raise ValueError(f"Invalid species_id: {row[field]}")
        else:
            if not isinstance(row[field], (int, float)):
                raise ValueError(f"Non-numeric value for {field}: {row[field]}")
            if row[field] <= 0:
                raise ValueError(f"Value for {field} must be > 0, got {row[field]}")
    
    return True

def aggregate_and_validate_metrics() -> pd.DataFrame:
    """
    Process images, aggregate results, and validate against schema.
    """
    logger.info(f"Starting RSA metrics generation from {INPUT_DIR}")
    
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}. Run T012 first.")
    
    # Process all images
    results = process_directory(INPUT_DIR)
    
    if not results:
        raise RuntimeError("No valid images were processed. Check logs for errors.")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    logger.info(f"Processed {len(df)} images. Validating metrics...")
    
    # Validate each row
    valid_rows = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            row_dict = row.to_dict()
            validate_row(row_dict)
            valid_rows.append(row_dict)
        except ValueError as e:
            errors.append(f"Row {idx}: {e}")
            logger.warning(f"Skipping invalid row: {e}")
    
    if errors:
        logger.warning(f"Found {len(errors)} invalid rows. Details logged.")
    
    if not valid_rows:
        raise RuntimeError("No valid rows found after validation. Pipeline halted.")
    
    final_df = pd.DataFrame(valid_rows)
    
    # Ensure correct column order and types
    final_df = final_df[['species_id', 'depth', 'branching_density', 'surface_area']]
    final_df['depth'] = final_df['depth'].astype(float)
    final_df['branching_density'] = final_df['branching_density'].astype(float)
    final_df['surface_area'] = final_df['surface_area'].astype(float)
    
    logger.info(f"Validation complete. {len(final_df)} valid records.")
    return final_df

def main():
    """Main entry point for T015."""
    try:
        # Ensure output directory exists
        ensure_directories()
        
        # Generate and validate data
        df = aggregate_and_validate_metrics()
        
        # Write to CSV
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False)
        
        logger.info(f"Successfully wrote validated metrics to {OUTPUT_FILE}")
        
        # Log summary
        logger.info(f"Summary: {len(df)} records, columns: {list(df.columns)}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
