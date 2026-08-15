import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_processed_dir, get_metadata_file
from utils.provenance import compute_file_hash, generate_provenance_record, save_provenance_record

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metadata(metadata_path: Path) -> dict:
    """Load the metadata YAML configuration."""
    import yaml
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}, creating empty structure.")
        return {"sources": {}}
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f) or {"sources": {}}

def save_metadata(metadata_path: Path, metadata: dict) -> None:
    """Save the metadata YAML configuration."""
    import yaml
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

def load_guild_source(source_path: Path) -> list:
    """
    Load the guild source CSV file.
    Expects columns: species_id, foraging_guild, and potentially source_citation.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Guild source file not found at {source_path}. "
                                "Please ensure T008a (download_guild_source.py) has run successfully.")
    
    logger.info(f"Loading guild source from {source_path}")
    rows = []
    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_fields = {'species_id', 'foraging_guild'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Guild source file missing required columns: {required_fields}. "
                             f"Found: {reader.fieldnames}")
        
        for row in reader:
            # Normalize keys if necessary (strip whitespace)
            cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
            rows.append(cleaned_row)
    
    if not rows:
        raise ValueError("Guild source file is empty.")
    
    logger.info(f"Loaded {len(rows)} records from guild source.")
    return rows

def validate_schema(rows: list) -> bool:
    """
    Validate that the loaded data conforms to the expected schema.
    Checks for presence of species_id and foraging_guild.
    """
    for i, row in enumerate(rows):
        if not row.get('species_id'):
            logger.error(f"Row {i} missing 'species_id'.")
            return False
        if not row.get('foraging_guild'):
            logger.error(f"Row {i} missing 'foraging_guild'.")
            return False
    return True

def save_mapping(output_path: Path, rows: list, source_citation: str, extraction_date: str) -> None:
    """
    Save the processed guild mapping to CSV.
    Columns: species_id, foraging_guild, source_citation, extraction_date
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                'species_id': row['species_id'],
                'foraging_guild': row['foraging_guild'],
                'source_citation': source_citation,
                'extraction_date': extraction_date
            })
    
    logger.info(f"Saved guild mapping to {output_path} ({len(rows)} rows).")

def record_provenance_in_metadata(metadata_path: Path, source_path: Path, output_path: Path, source_citation: str):
    """
    Update data/metadata.yaml with provenance for the generated guild mapping.
    """
    metadata = load_metadata(metadata_path)
    
    if 'sources' not in metadata:
        metadata['sources'] = {}
    
    artifact_name = 'guild_mapping'
    record = {
        'input_file': str(source_path.relative_to(project_root)),
        'input_hash': compute_file_hash(source_path),
        'output_file': str(output_path.relative_to(project_root)),
        'output_hash': compute_file_hash(output_path),
        'source_citation': source_citation,
        'generated_at': datetime.now().isoformat(),
        'script': 'data/generate_guild_mapping.py'
    }
    
    metadata['sources'][artifact_name] = record
    save_metadata(metadata_path, metadata)
    logger.info(f"Recorded provenance for {artifact_name} in metadata.yaml.")

def main():
    """
    Main entry point for generating the guild mapping.
    1. Load metadata to find source citation URL/ID.
    2. Load the raw guild source CSV (T008a output).
    3. Validate schema.
    4. Extract species_id and foraging_guild.
    5. Add provenance columns (source_citation, extraction_date).
    6. Save to data/processed/guild_mapping.csv.
    7. Update metadata.yaml.
    """
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_dir()
    metadata_path = get_metadata_file()
    
    input_file = raw_dir / "guild_source.csv"
    output_file = processed_dir / "guild_mapping.csv"
    
    logger.info("Starting guild mapping generation (T008b)...")
    
    # Load metadata to get source citation details
    metadata = load_metadata(metadata_path)
    source_citation = "Birds of the World" # Default fallback if not explicitly found, though T008a should ensure this
    if 'sources' in metadata and 'guild_source' in metadata['sources']:
        # Attempt to extract citation from the previous step's metadata if available
        citation_data = metadata['sources']['guild_source']
        if 'source_citation' in citation_data:
            source_citation = citation_data['source_citation']
        elif 'url' in citation_data:
            source_citation = citation_data['url']
    
    # Load raw data
    try:
        rows = load_guild_source(input_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Validate schema
    if not validate_schema(rows):
        logger.error("Schema validation failed. Aborting.")
        sys.exit(1)
    
    # Generate provenance timestamp
    extraction_date = datetime.now().strftime("%Y-%m-%d")
    
    # Save the mapping
    save_mapping(output_file, rows, source_citation, extraction_date)
    
    # Record provenance
    record_provenance_in_metadata(metadata_path, input_file, output_file, source_citation)
    
    logger.info("T008b completed successfully.")

if __name__ == "__main__":
    main()
