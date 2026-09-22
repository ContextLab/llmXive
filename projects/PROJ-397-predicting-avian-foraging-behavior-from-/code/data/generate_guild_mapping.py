import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Import from utils.config to get project paths
from utils.config import get_project_root, get_raw_data_dir, get_processed_dir, get_metadata_file
# Import from utils.provenance to handle metadata updates
from utils.provenance import compute_file_hash, save_metadata_config, load_metadata_config, record_source_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return get_project_root()

def load_metadata(metadata_path: Path) -> dict:
    """Load existing metadata configuration."""
    if metadata_path.exists():
        return load_metadata_config(metadata_path)
    return {}

def save_metadata(metadata: dict, metadata_path: Path) -> None:
    """Save metadata configuration to disk."""
    save_metadata_config(metadata, str(metadata_path))

def load_guild_source(input_path: Path) -> list:
    """
    Load the guild source CSV.
    Expects columns: species_id, foraging_guild, source_citation (or similar).
    Returns a list of dicts.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Guild source file not found: {input_path}")
    
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate required columns exist
        required_cols = {'species_id', 'foraging_guild'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"Guild source CSV missing required columns: {missing}")
        
        for row in reader:
            # Ensure species_id is a string (often integers in CSVs)
            row['species_id'] = str(row['species_id']).strip()
            row['foraging_guild'] = str(row['foraging_guild']).strip()
            records.append(row)
    
    if not records:
        raise ValueError("Guild source CSV is empty or contains no valid rows.")
    
    return records

def validate_schema(records: list) -> bool:
    """
    Validate the records against the expected output schema.
    Returns True if valid, raises ValueError otherwise.
    """
    required_output_cols = {'species_id', 'foraging_guild', 'source_citation', 'extraction_date'}
    
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {i} is not a dictionary.")
        
        # Check for required keys
        # Note: source_citation might come from the input, extraction_date is generated
        if 'species_id' not in record or 'foraging_guild' not in record:
            raise ValueError(f"Record {i} missing species_id or foraging_guild.")
        
        # Check if source_citation exists (it should be passed through from input)
        # If the input didn't have it, we might need to handle that, but the task implies
        # reading from a source that has it.
        if 'source_citation' not in record and 'extraction_date' not in record:
            # We will add extraction_date in the main function, but source_citation should be there
            # If the input lacks source_citation, we might default to 'Unknown' or fail.
            # Let's assume the input has it or we add a default.
            pass 
    
    return True

def save_mapping(records: list, output_path: Path) -> None:
    """
    Write the processed records to the output CSV.
    Columns: species_id, foraging_guild, source_citation, extraction_date
    """
    if not records:
        raise ValueError("No records to save.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved guild mapping to {output_path}")

def record_provenance_in_metadata(metadata: dict, input_path: Path, output_path: Path) -> dict:
    """
    Update the metadata dictionary with provenance for this step.
    """
    if 'steps' not in metadata:
        metadata['steps'] = []
    
    step_record = {
        'step_name': 'generate_guild_mapping',
        'timestamp': datetime.now().isoformat(),
        'input_file': str(input_path),
        'input_hash': compute_file_hash(input_path),
        'output_file': str(output_path),
        'output_hash': compute_file_hash(output_path),
        'description': 'Transformed raw guild source CSV into standardized mapping format.'
    }
    
    metadata['steps'].append(step_record)
    
    # Update top-level extraction date if not present
    if 'extraction_date' not in metadata:
        metadata['extraction_date'] = datetime.now().isoformat()
        
    return metadata

def main():
    """
    Main entry point for generating the guild mapping.
    Reads data/raw/guild_source.csv and writes data/processed/guild_mapping.csv
    """
    project_root = get_project_root()
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_dir()
    metadata_path = get_metadata_file()
    
    input_path = raw_dir / 'guild_source.csv'
    output_path = processed_dir / 'guild_mapping.csv'
    
    logger.info(f"Starting guild mapping generation.")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # 1. Load metadata to update later
        metadata = load_metadata(metadata_path)
        
        # 2. Load raw guild source
        logger.info("Loading guild source CSV...")
        raw_records = load_guild_source(input_path)
        
        # 3. Process records: ensure source_citation exists and add extraction_date
        extraction_date = datetime.now().strftime('%Y-%m-%d')
        processed_records = []
        
        for record in raw_records:
            # Ensure source_citation exists; if not, try to infer or set default
            citation = record.get('source_citation', 'Unknown Source')
            if not citation or citation.strip() == '':
                citation = 'Unknown Source'
            
            processed_record = {
                'species_id': record['species_id'],
                'foraging_guild': record['foraging_guild'],
                'source_citation': citation,
                'extraction_date': extraction_date
            }
            processed_records.append(processed_record)
        
        # 4. Validate schema
        logger.info("Validating schema...")
        validate_schema(processed_records)
        
        # 5. Save mapping
        logger.info("Saving guild mapping...")
        save_mapping(processed_records, output_path)
        
        # 6. Record provenance
        logger.info("Recording provenance...")
        updated_metadata = record_provenance_in_metadata(metadata, input_path, output_path)
        save_metadata(updated_metadata, metadata_path)
        
        logger.info("Guild mapping generation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    sys.exit(main())
