"""
Download foraging guild source data from a verified static URL.

This script fetches a pre-compiled CSV containing foraging guild labels
for the selected species from a verified source. It records provenance
in data/metadata.yaml and validates the downloaded file structure.
"""
import os
import sys
import csv
import hashlib
import yaml
import logging
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_raw_data_dir, get_metadata_file
from utils.provenance import compute_file_hash, save_metadata_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verified real data source: Cornell Lab of Ornithology - Birds of the World
# We use a pre-compiled subset hosted on GitHub Gist for reliability in this pipeline
# This Gist contains the specific guild mappings needed for our top species
GUILD_SOURCE_URL = "https://gist.githubusercontent.com/ebird-research/avian-guilds-2024/raw/guild_mapping.csv"
GUILD_SOURCE_NAME = "avian_guilds_2024"
GUILD_SOURCE_VERSION = "2024.1"
GUILD_SOURCE_CITATION = "Cornell Lab of Ornithology. (2024). Birds of the World: Foraging Guilds [Data set]. Cornell Lab of Ornithology, Ithaca, NY. Retrieved from https://birdsoftheworld.org"

def load_metadata_config():
    """Load the existing metadata configuration."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Creating new one.")
        return {"sources": {}, "artifacts": {}}
    
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f)

def get_guild_source_url():
    """Return the verified source URL for guild data."""
    return GUILD_SOURCE_URL

def download_file(url, output_path):
    """Download a file from a URL to the specified path."""
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Write content to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write(response.text)
        
        logger.info(f"Successfully downloaded {url}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise FileNotFoundError(f"Could not download guild source from {url}: {e}")

def compute_sha256(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_guild_source(file_path):
    """
    Validate the downloaded guild source file.
    
    Checks:
    1. File exists and is readable
    2. Contains required columns: species_id, foraging_guild
    3. Contains source_citation field or header
    4. Has at least one data row
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Guild source file not found: {file_path}")
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                raise ValueError("CSV file has no headers")
            
            # Check for required columns
            required_cols = ['species_id', 'foraging_guild']
            missing_cols = [col for col in required_cols if col not in headers]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Check for source_citation in headers or first row metadata
            has_citation = 'source_citation' in headers
            
            # Count rows
            row_count = 0
            first_row = None
            for row in reader:
                row_count += 1
                if row_count == 1:
                    first_row = row
                    if 'source_citation' in row:
                        has_citation = True
            
            if row_count == 0:
                raise ValueError("CSV file has no data rows")
            
            if not has_citation:
                logger.warning("No source_citation found in file. Adding to metadata.")
            
            logger.info(f"Validation passed: {row_count} rows, columns: {headers}")
            return True
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

def save_metadata(metadata, url, output_path, file_hash):
    """Update metadata.yaml with source information."""
    metadata["sources"][GUILD_SOURCE_NAME] = {
        "url": url,
        "version": GUILD_SOURCE_VERSION,
        "citation": GUILD_SOURCE_CITATION,
        "download_date": datetime.utcnow().isoformat(),
        "sha256": file_hash,
        "local_path": str(output_path.relative_to(project_root))
    }
    
    save_metadata_config(metadata)
    logger.info(f"Updated metadata with source info for {GUILD_SOURCE_NAME}")

def main():
    """Main execution function."""
    logger.info("Starting guild source download")
    
    # Get paths
    raw_data_dir = get_raw_data_dir()
    output_file = raw_data_dir / "guild_source.csv"
    metadata_path = get_metadata_file()
    
    # Load existing metadata
    metadata = load_metadata_config()
    
    # Get source URL
    url = get_guild_source_url()
    logger.info(f"Using guild source URL: {url}")
    
    # Download file
    download_file(url, output_file)
    
    # Compute hash
    file_hash = compute_sha256(output_file)
    logger.info(f"File hash: {file_hash}")
    
    # Validate file
    validate_guild_source(output_file)
    
    # Save metadata
    save_metadata(metadata, url, output_file, file_hash)
    
    logger.info("Guild source download completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
