import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_raw_data_dir, get_processed_dir
from utils.provenance import load_metadata_config, save_metadata_config, compute_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metadata():
    """Load the project metadata configuration."""
    metadata_path = get_data_dir() / "metadata.yaml"
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Creating new one.")
        return {}
    return load_metadata_config(metadata_path)

def save_metadata(metadata):
    """Save the updated metadata configuration."""
    metadata_path = get_data_dir() / "metadata.yaml"
    save_metadata_config(metadata_path, metadata)

def load_guild_source():
    """
    Load the guild source CSV file.
    
    Returns:
        list of dicts: Rows from the CSV file.
        
    Raises:
        FileNotFoundError: If the source file does not exist.
        ValueError: If the required 'source_citation' column is missing.
    """
    source_path = get_raw_data_dir() / "guild_source.csv"
    if not source_path.exists():
        raise FileNotFoundError(
            f"Guild source file not found at {source_path}. "
            "Please run data/download_guild_source.py first."
        )
    
    logger.info(f"Loading guild source from {source_path}")
    rows = []
    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'source_citation' not in reader.fieldnames:
            raise ValueError(
                f"Guild source CSV missing required column 'source_citation'. "
                f"Found columns: {reader.fieldnames}"
            )
        for row in reader:
            rows.append(row)
    
    if not rows:
        logger.warning("Guild source CSV is empty.")
        
    return rows

def validate_schema(rows):
    """
    Validate that the loaded rows have the expected structure.
    
    Args:
        rows: List of dictionaries loaded from the source CSV.
        
    Returns:
        bool: True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    if not rows:
        raise ValueError("Input data is empty.")
    
    required_keys = {'species_id', 'foraging_guild', 'source_citation'}
    first_row_keys = set(rows[0].keys())
    
    missing = required_keys - first_row_keys
    if missing:
        raise ValueError(f"Input data missing required keys: {missing}")
        
    for i, row in enumerate(rows):
        if not row.get('species_id'):
            raise ValueError(f"Row {i} has empty or missing 'species_id'")
        if not row.get('foraging_guild'):
            raise ValueError(f"Row {i} has empty or missing 'foraging_guild'")
        
    return True

def save_mapping(rows, extraction_date):
    """
    Save the processed guild mapping to the processed directory.
    
    Args:
        rows: List of dictionaries containing guild data.
        extraction_date: ISO format date string for the extraction timestamp.
        
    Returns:
        Path: Path to the saved file.
    """
    output_dir = get_processed_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "guild_mapping.csv"
    
    logger.info(f"Writing guild mapping to {output_path}")
    
    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            new_row = {
                'species_id': row['species_id'],
                'foraging_guild': row['foraging_guild'],
                'source_citation': row['source_citation'],
                'extraction_date': extraction_date
            }
            writer.writerow(new_row)
            
    return output_path

def record_provenance_in_metadata(metadata, input_path, output_path):
    """
    Record the provenance of the guild mapping generation in the metadata.
    
    Args:
        metadata: The metadata dictionary to update.
        input_path: Path to the input source file.
        output_path: Path to the generated output file.
        
    Returns:
        dict: Updated metadata.
    """
    timestamp = datetime.utcnow().isoformat()
    file_hash = compute_file_hash(output_path)
    
    step_record = {
        "step": "generate_guild_mapping",
        "timestamp": timestamp,
        "input_file": str(input_path),
        "output_file": str(output_path),
        "output_hash": file_hash,
        "status": "success"
    }
    
    if "pipeline_steps" not in metadata:
        metadata["pipeline_steps"] = []
    metadata["pipeline_steps"].append(step_record)
    
    # Update the specific artifact record if it exists, or create new
    if "artifacts" not in metadata:
        metadata["artifacts"] = {}
        
    metadata["artifacts"]["guild_mapping"] = {
        "path": str(output_path),
        "hash": file_hash,
        "created_at": timestamp,
        "source": str(input_path)
    }
    
    return metadata

def main():
    """Main entry point for the guild mapping generation script."""
    logger.info("Starting guild mapping generation...")
    
    try:
        # 1. Load Metadata
        metadata = load_metadata()
        
        # 2. Load Guild Source
        guild_rows = load_guild_source()
        
        # 3. Validate Schema
        validate_schema(guild_rows)
        
        # 4. Determine Extraction Date (use current time for this transformation step)
        extraction_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 5. Save Mapping
        output_path = save_mapping(guild_rows, extraction_date)
        
        # 6. Record Provenance
        input_path = get_raw_data_dir() / "guild_source.csv"
        updated_metadata = record_provenance_in_metadata(metadata, input_path, output_path)
        save_metadata(updated_metadata)
        
        logger.info(f"Successfully generated guild mapping: {output_path}")
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
