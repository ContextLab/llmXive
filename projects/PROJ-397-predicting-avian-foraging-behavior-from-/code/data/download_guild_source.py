"""
T008a: Download 'Birds of the World' foraging guild data.

Fetches the external literature source defined in data/metadata.yaml,
validates the presence of required fields, and saves to data/raw/guild_source.csv.
"""
import os
import sys
import csv
import hashlib
import yaml
import logging
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config import get_data_dir, get_raw_data_dir, get_metadata_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_metadata_config():
    """Load the metadata.yaml configuration file."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f)

def get_guild_source_url(metadata_config):
    """
    Extract the guild source URL from metadata.
    Expects metadata['external_sources']['birds_of_the_world']['url']
    """
    try:
        return metadata_config['external_sources']['birds_of_the_world']['url']
    except KeyError:
        raise KeyError("Missing 'external_sources.birds_of_the_world.url' in metadata.yaml")

def download_file(url, output_path):
    """
    Download a file from a URL.
    Raises an exception if the download fails (no silent fallback).
    """
    logger.info(f"Downloading {url} to {output_path}")
    try:
        # Use a reasonable timeout
        urllib.request.urlretrieve(url, output_path, reporthook=urllib.request._urlopen)
    except urllib.error.URLError as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise FileNotFoundError(f"Real data source unavailable: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        raise e
    
    if not output_path.exists():
        raise FileNotFoundError(f"Downloaded file not found at {output_path}")
    
    logger.info(f"Download complete: {output_path}")

def compute_sha256(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata_config, file_path, source_url, file_hash, extraction_date):
    """Update metadata.yaml with the new source record."""
    # Ensure structure exists
    if 'external_sources' not in metadata_config:
        metadata_config['external_sources'] = {}
    
    metadata_config['external_sources']['birds_of_the_world'] = {
        'url': source_url,
        'file_path': str(file_path),
        'sha256': file_hash,
        'extraction_date': extraction_date,
        'citation': 'Cornell Lab of Ornithology. (2023). Birds of the World. Cornell Lab of Ornithology, Ithaca, NY, USA.'
    }

    with open(get_metadata_file(), 'w') as f:
        yaml.dump(metadata_config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated metadata at {get_metadata_file()}")

def validate_guild_source(file_path):
    """
    Verify the downloaded file contains the required 'source_citation' field
    and valid structure.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Guild source file missing: {file_path}")

    # Determine format based on extension (support CSV, JSON, XML as per task)
    ext = file_path.suffix.lower()
    has_citation = False
    row_count = 0

    if ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Check header for required field
            if 'source_citation' not in reader.fieldnames:
                raise ValueError("CSV file missing required column 'source_citation'")
            
            # Validate at least one row exists and has the citation
            for row in reader:
                row_count += 1
                if row.get('source_citation') and 'Birds of the World' in row['source_citation']:
                    has_citation = True
                    break # Found at least one valid record
    
    elif ext == '.json':
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                if len(data) == 0:
                    raise ValueError("JSON file is empty")
                if 'source_citation' not in data[0]:
                    raise ValueError("JSON file missing required key 'source_citation'")
                for item in data:
                    row_count += 1
                    if 'Birds of the World' in str(item.get('source_citation', '')):
                        has_citation = True
                        break
            else:
                raise ValueError("JSON root must be a list of records")
    
    elif ext == '.xml':
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Assuming a standard structure where <record> contains the data
        records = root.findall('.//record')
        if not records:
            # Try finding any element with source_citation
            records = root.findall('.//source_citation')
        
        if not records:
            raise ValueError("XML file contains no records")
        
        for elem in records:
            row_count += 1
            # Check if this element is the citation or contains it
            if 'Birds of the World' in str(elem.text) or elem.find('source_citation') is not None:
                has_citation = True
                break
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if not has_citation:
        raise ValueError("Downloaded file does not contain 'Birds of the World' in 'source_citation' field.")
    
    if row_count == 0:
        raise ValueError("Downloaded file contains no data rows.")

    logger.info(f"Validation passed: {row_count} rows found, citation verified.")
    return True

def main():
    """Main entry point for T008a."""
    logger.info("Starting T008a: Download Guild Source")
    
    # 1. Load metadata to get URL
    metadata_config = load_metadata_config()
    source_url = get_guild_source_url(metadata_config)
    
    # 2. Define output path
    raw_dir = get_raw_data_dir()
    output_file = raw_dir / "guild_source.csv"
    
    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Download
    download_file(source_url, output_file)
    
    # 4. Compute hash
    file_hash = compute_sha256(output_file)
    
    # 5. Validate content
    validate_guild_source(output_file)
    
    # 6. Update metadata
    extraction_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_metadata(metadata_config, output_file, source_url, file_hash, extraction_date)
    
    logger.info("T008a completed successfully.")

if __name__ == "__main__":
    main()
