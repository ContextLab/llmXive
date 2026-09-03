"""
T008b: Generate guild mapping from downloaded source.

Loads the 'Birds of the World' foraging guild data downloaded by T008a
(data/raw/guild_source.csv), extracts species_id and foraging_guild,
and saves a processed mapping file with provenance fields to
data/processed/guild_mapping.csv.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_data_dir, get_processed_dir, get_raw_data_dir
from utils.provenance import compute_file_hash, generate_provenance_record, save_provenance_record

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE_NAME = "guild_source.csv"
OUTPUT_FILE_NAME = "guild_mapping.csv"
REQUIRED_COLUMNS = ['species_id', 'foraging_guild', 'source_citation']

def load_metadata():
    """Load the metadata.yaml file to get provenance info."""
    data_dir = get_data_dir()
    metadata_path = data_dir / "metadata.yaml"
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Provenance may be incomplete.")
        return {}
    
    import yaml
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_metadata(metadata):
    """Save the updated metadata.yaml file."""
    data_dir = get_data_dir()
    metadata_path = data_dir / "metadata.yaml"
    import yaml
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def load_guild_source(input_path):
    """
    Load the guild source CSV and validate it contains required columns.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries representing the rows.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Guild source file not found: {input_path}")
    
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate columns
        if reader.fieldnames is None:
            raise ValueError("Guild source file is empty or has no header.")
        
        missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Guild source file missing required columns: {missing_cols}")
        
        for row in reader:
            rows.append(row)
    
    logger.info(f"Loaded {len(rows)} records from {input_path}")
    return rows

def validate_schema(rows):
    """
    Validate the data schema before processing.
    
    Args:
        rows: List of dictionaries.
        
    Raises:
        ValueError: If validation fails.
    """
    if not rows:
        raise ValueError("No data rows found in guild source.")
    
    for i, row in enumerate(rows):
        species_id = row.get('species_id', '').strip()
        guild = row.get('foraging_guild', '').strip()
        
        if not species_id:
            raise ValueError(f"Row {i}: Missing or empty species_id.")
        if not guild:
            logger.warning(f"Row {i}: Missing or empty foraging_guild for {species_id}. Skipping.")
            rows[i] = None  # Mark for removal
    
    # Remove invalid rows
    valid_rows = [r for r in rows if r is not None]
    if len(valid_rows) < len(rows):
        logger.info(f"Removed {len(rows) - len(valid_rows)} invalid rows.")
    
    return valid_rows

def save_mapping(rows, output_path):
    """
    Save the processed guild mapping to CSV.
    
    Args:
        rows: List of validated row dictionaries.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        now = datetime.utcnow().isoformat() + "Z"
        for row in rows:
            writer.writerow({
                'species_id': row['species_id'].strip(),
                'foraging_guild': row['foraging_guild'].strip(),
                'source_citation': row.get('source_citation', 'Birds of the World').strip(),
                'extraction_date': now
            })
    
    logger.info(f"Saved {len(rows)} records to {output_path}")

def record_provenance_in_metadata(input_path, output_path, metadata):
    """
    Record provenance information in metadata.yaml.
    
    Args:
        input_path: Path to input file.
        output_path: Path to output file.
        metadata: Existing metadata dictionary.
    """
    if 'provenance' not in metadata:
        metadata['provenance'] = {}
    
    step_name = "T008b_generate_guild_mapping"
    record = generate_provenance_record(
        step_name=step_name,
        input_files=[str(input_path)],
        output_files=[str(output_path)],
        script_path=str(Path(__file__).relative_to(PROJECT_ROOT))
    )
    
    if step_name not in metadata['provenance']:
        metadata['provenance'][step_name] = []
    metadata['provenance'][step_name].append(record)
    
    # Also update the specific artifact record if it exists
    if 'artifacts' not in metadata:
        metadata['artifacts'] = {}
    
    artifact_key = str(output_path.relative_to(get_data_dir()))
    metadata['artifacts'][artifact_key] = {
        'source': str(input_path.relative_to(get_data_dir())),
        'hash': compute_file_hash(output_path),
        'generated_at': datetime.utcnow().isoformat() + "Z"
    }

def main():
    """Main entry point for T008b."""
    logger.info("Starting T008b: Generate Guild Mapping")
    
    # Paths
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_dir()
    input_path = raw_dir / INPUT_FILE_NAME
    output_path = processed_dir / OUTPUT_FILE_NAME
    
    # Load metadata
    metadata = load_metadata()
    
    try:
        # Load source
        logger.info(f"Loading guild source from {input_path}")
        rows = load_guild_source(input_path)
        
        # Validate
        logger.info("Validating schema...")
        valid_rows = validate_schema(rows)
        
        # Save
        logger.info(f"Saving mapping to {output_path}")
        save_mapping(valid_rows, output_path)
        
        # Record provenance
        logger.info("Recording provenance...")
        record_provenance_in_metadata(input_path, output_path, metadata)
        save_metadata(metadata)
        
        logger.info("T008b completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
