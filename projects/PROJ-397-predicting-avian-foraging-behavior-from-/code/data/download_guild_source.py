"""
Script to generate guild mapping source file.

This script reads a manually curated CSV file containing species-to-guild mappings
derived from authoritative ornithological literature (e.g., Birds of the World).
It validates the input, copies it to the processed output location with a standardized
filename, and records provenance metadata.

If the manual input file is missing, this script raises FileNotFoundError immediately.
No fallback to external URLs or synthetic data is permitted.
"""
import os
import sys
import csv
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_project_root
from utils.provenance import compute_file_hash, save_provenance_record

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILENAME = "guild_mapping_manual.csv"
OUTPUT_FILENAME = "guild_source.csv"
REQUIRED_COLUMNS = ["species_id", "foraging_guild", "source_citation"]
SOURCE_CITATION = "Birds of the World (Cornell Lab of Ornithology)"

def get_input_file_path() -> Path:
    """
    Return the expected path for the manually curated input file.
    
    The file is expected to be in the data/raw directory with the specific name.
    """
    raw_dir = get_raw_data_dir()
    return raw_dir / INPUT_FILENAME

def get_output_file_path() -> Path:
    """
    Return the expected path for the output guild source file.
    """
    raw_dir = get_raw_data_dir()
    return raw_dir / OUTPUT_FILENAME

def validate_guild_source(input_path: Path) -> None:
    """
    Validate the structure and content of the guild source file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file structure is invalid or columns are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required manual guild mapping file not found: {input_path}. "
            "Please curate 'guild_mapping_manual.csv' in the data/raw directory "
            "with columns: species_id, foraging_guild, source_citation."
        )
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                raise ValueError("Input file is empty or has no headers.")
            
            missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_cols:
                raise ValueError(
                    f"Input file missing required columns: {missing_cols}. "
                    f"Required: {REQUIRED_COLUMNS}"
                )
            
            # Check for at least one data row
            rows = list(reader)
            if not rows:
                raise ValueError("Input file contains no data rows.")
            
            # Validate data content
            for i, row in enumerate(rows):
                if not row['species_id'] or not row['foraging_guild']:
                    raise ValueError(
                        f"Row {i+2} (0-indexed {i}) has empty species_id or foraging_guild."
                    )
            
            logger.info(f"Validation passed: {len(rows)} records found.")
            
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")

def process_guild_source(input_path: Path, output_path: Path) -> int:
    """
    Process the guild source file: copy with potential normalization.
    
    Args:
        input_path: Path to input file.
        output_path: Path to output file.
        
    Returns:
        Number of records processed.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read and write with explicit encoding and normalization
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=REQUIRED_COLUMNS)
        
        writer.writeheader()
        count = 0
        for row in reader:
            # Normalize whitespace
            normalized_row = {
                'species_id': row['species_id'].strip(),
                'foraging_guild': row['foraging_guild'].strip(),
                'source_citation': row.get('source_citation', SOURCE_CITATION).strip()
            }
            writer.writerow(normalized_row)
            count += 1
    
    logger.info(f"Processed {count} records to {output_path}")
    return count

def save_metadata(output_path: Path, record_count: int) -> None:
    """
    Record provenance metadata for the generated file.
    
    Args:
        output_path: Path to the generated file.
        record_count: Number of records in the file.
    """
    metadata_path = get_project_root() / "data" / "metadata.yaml"
    
    # Compute hash
    file_hash = compute_file_hash(output_path)
    
    # Load existing metadata or create new
    metadata = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}
        except (yaml.YAMLError, IOError) as e:
            logger.warning(f"Could not load existing metadata: {e}")
            metadata = {}
    
    # Create provenance record
    record = {
        "file": output_path.name,
        "path": str(output_path),
        "sha256": file_hash,
        "source": f"Manual curation from {SOURCE_CITATION}",
        "input_file": INPUT_FILENAME,
        "record_count": record_count,
        "extraction_date": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "description": "Manually curated foraging guild mappings for avian species"
    }
    
    # Update metadata
    if "guild_source" not in metadata:
        metadata["guild_source"] = {}
    metadata["guild_source"]["latest"] = record
    
    # Save metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Metadata saved to {metadata_path}")

def main() -> int:
    """
    Main entry point for the guild source generation script.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        input_path = get_input_file_path()
        output_path = get_output_file_path()
        
        logger.info(f"Looking for input file at: {input_path}")
        
        # Validate input (raises FileNotFoundError if missing)
        validate_guild_source(input_path)
        
        # Process file
        record_count = process_guild_source(input_path, output_path)
        
        # Save metadata
        save_metadata(output_path, record_count)
        
        logger.info(f"Successfully generated {output_path} with {record_count} records.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        # Re-raise to ensure the pipeline fails loudly as required
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
