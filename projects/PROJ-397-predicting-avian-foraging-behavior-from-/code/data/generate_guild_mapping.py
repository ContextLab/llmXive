"""
T008b: Generate the final guild mapping CSV from the manual source.

Reads data/raw/guild_source.csv and writes data/processed/guild_mapping.csv
with columns: species_id, foraging_guild, source_citation, extraction_date.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Import project utilities from the API surface
from utils.config import get_processed_dir, get_raw_data_dir, get_project_root
from utils.provenance import record_source_info, compute_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_input_file_path() -> Path:
    """Return the path to the manual guild source CSV."""
    raw_dir = get_raw_data_dir()
    return raw_dir / "guild_source.csv"

def get_output_file_path() -> Path:
    """Return the path for the processed guild mapping CSV."""
    processed_dir = get_processed_dir()
    return processed_dir / "guild_mapping.csv"

def load_guild_source(input_path: Path) -> list:
    """
    Load the manual guild source CSV.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries representing rows.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Guild source file not found: {input_path}. "
            "Please ensure T008a has generated data/raw/guild_source.csv."
        )
    
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'species_id', 'foraging_guild', 'source_citation'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Input CSV missing required columns. "
                f"Expected: {required_cols}, Found: {reader.fieldnames}"
            )
        
        for row in reader:
            rows.append(row)
    
    logger.info(f"Loaded {len(rows)} rows from {input_path}")
    return rows

def validate_schema(data: list) -> bool:
    """
    Validate the data against the expected schema.
    
    Args:
        data: List of row dictionaries.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    if not data:
        raise ValueError("Data list is empty.")
    
    for i, row in enumerate(data):
        if not row.get('species_id'):
            raise ValueError(f"Row {i} missing 'species_id'.")
        if not row.get('foraging_guild'):
            raise ValueError(f"Row {i} missing 'foraging_guild'.")
        if not row.get('source_citation'):
            raise ValueError(f"Row {i} missing 'source_citation'.")
    
    return True

def save_mapping(data: list, output_path: Path) -> None:
    """
    Save the processed guild mapping to CSV.
    
    Args:
        data: List of row dictionaries.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    extraction_date = datetime.now().strftime('%Y-%m-%d')
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            row['extraction_date'] = extraction_date
            writer.writerow(row)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def record_provenance_in_metadata(input_path: Path, output_path: Path) -> None:
    """
    Record provenance information for the generated mapping in metadata.
    
    Args:
        input_path: Path to the source file.
        output_path: Path to the generated file.
    """
    from utils.provenance import load_metadata_config, save_metadata_config
    
    metadata = load_metadata_config()
    
    # Compute hash of output
    output_hash = compute_file_hash(output_path)
    
    # Record the transformation
    step_record = {
        "step": "T008b_generate_guild_mapping",
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "input_hash": compute_file_hash(input_path),
        "output_file": str(output_path),
        "output_hash": output_hash,
        "script": "data/generate_guild_mapping.py"
    }
    
    if "steps" not in metadata:
        metadata["steps"] = []
    metadata["steps"].append(step_record)
    
    save_metadata_config(metadata)
    logger.info("Provenance recorded in metadata.yaml")

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        input_path = get_input_file_path()
        output_path = get_output_file_path()
        
        logger.info(f"Processing guild mapping from {input_path} to {output_path}")
        
        # Load
        data = load_guild_source(input_path)
        
        # Validate
        validate_schema(data)
        
        # Save
        save_mapping(data, output_path)
        
        # Record provenance
        record_provenance_in_metadata(input_path, output_path)
        
        logger.info("Task T008b completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
