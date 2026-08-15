"""
Download the 'Birds of the World' foraging guild data from a verified static source.

This task satisfies FR-001 and Constitution Principle VI by explicitly downloading
the external literature source and verifying its provenance.

The source URL is configurable via data/metadata.yaml.
Supports CSV, JSON, or XML formats.
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
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_metadata_file, get_raw_data_dir, get_project_root
from utils.provenance import compute_file_hash, record_artifact_provenance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
SUPPORTED_FORMATS = ['.csv', '.json', '.xml']
REQUIRED_FIELDS = ['source_citation']
EXPECTED_CITATION = 'Birds of the World'

def load_metadata_config() -> Dict[str, Any]:
    """Load metadata configuration from YAML file."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_guild_source_url(metadata: Dict[str, Any]) -> str:
    """Extract the guild source URL from metadata configuration."""
    try:
        # Look for the source URL in the metadata under 'sources' or 'data_sources'
        sources = metadata.get('sources', {})
        guild_source = sources.get('guild', {}) or sources.get('birds_of_the_world', {})
        
        if isinstance(guild_source, dict):
            url = guild_source.get('url')
            if url:
                return url
        
        # Fallback: look for a direct URL key
        url = metadata.get('guild_source_url') or metadata.get('birds_of_the_world_url')
        if url:
            return url
        
        raise ValueError("No guild source URL found in metadata configuration")
    except Exception as e:
        logger.error(f"Failed to extract guild source URL from metadata: {e}")
        raise

def download_file(url: str, output_path: Path) -> None:
    """
    Download a file from a URL to the specified output path.
    
    Args:
        url: The URL to download from
        output_path: Local path to save the file
        
    Raises:
        requests.RequestException: If download fails
        ValueError: If the downloaded content is empty
    """
    logger.info(f"Downloading guild source from: {url}")
    
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        # Verify we got content
        if not response.content:
            raise ValueError("Downloaded content is empty")
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded to: {output_path}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during download: {e}")
        raise

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """Save updated metadata to YAML file."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(metadata, f, default_flow_style=False, sort_keys=False)

def validate_guild_source(file_path: Path) -> None:
    """
    Validate that the downloaded file contains required fields.
    
    Args:
        file_path: Path to the downloaded guild source file
        
    Raises:
        ValueError: If validation fails
    """
    logger.info(f"Validating guild source file: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Guild source file not found: {file_path}")
    
    # Determine file format
    suffix = file_path.suffix.lower()
    
    if suffix == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                raise ValueError("CSV file has no headers")
            
            # Check for required field
            if 'source_citation' not in headers:
                raise ValueError(
                    f"CSV file missing required 'source_citation' field. "
                    f"Available fields: {headers}"
                )
            
            # Verify citation content
            for row in reader:
                citation = row.get('source_citation', '')
                if EXPECTED_CITATION.lower() in citation.lower():
                    logger.info(f"Verified source citation: {citation}")
                    return
            
            raise ValueError(
                f"No row with expected citation '{EXPECTED_CITATION}' found in CSV"
            )
    
    elif suffix == '.json':
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            if len(data) == 0:
                raise ValueError("JSON array is empty")
            if not isinstance(data[0], dict):
                raise ValueError("JSON array elements are not objects")
            
            if 'source_citation' not in data[0]:
                raise ValueError(
                    f"JSON object missing required 'source_citation' field. "
                    f"Available fields: {list(data[0].keys())}"
                )
            
            citation = data[0].get('source_citation', '')
            if EXPECTED_CITATION.lower() in citation.lower():
                logger.info(f"Verified source citation: {citation}")
                return
            else:
                raise ValueError(
                    f"Source citation '{citation}' does not match expected '{EXPECTED_CITATION}'"
                )
        
        elif isinstance(data, dict):
            if 'source_citation' not in data:
                raise ValueError(
                    f"JSON object missing required 'source_citation' field. "
                    f"Available fields: {list(data.keys())}"
                )
            
            citation = data.get('source_citation', '')
            if EXPECTED_CITATION.lower() in citation.lower():
                logger.info(f"Verified source citation: {citation}")
                return
            else:
                raise ValueError(
                    f"Source citation '{citation}' does not match expected '{EXPECTED_CITATION}'"
                )
        
        else:
            raise ValueError("JSON file is not an array or object")
    
    elif suffix == '.xml':
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Try to find source_citation element
        citation_elem = root.find('.//source_citation')
        if citation_elem is None:
            # Try alternative names
            citation_elem = root.find('.//citation')
        
        if citation_elem is None:
            raise ValueError("XML file missing required 'source_citation' element")
        
        citation = citation_elem.text or ""
        if EXPECTED_CITATION.lower() in citation.lower():
            logger.info(f"Verified source citation: {citation}")
            return
        else:
            raise ValueError(
                f"Source citation '{citation}' does not match expected '{EXPECTED_CITATION}'"
            )
    
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def main():
    """Main entry point for downloading guild source data."""
    logger.info("Starting guild source download process")
    
    try:
        # Load metadata configuration
        metadata = load_metadata_config()
        
        # Get source URL from metadata
        url = get_guild_source_url(metadata)
        logger.info(f"Using guild source URL: {url}")
        
        # Define output path
        raw_data_dir = get_raw_data_dir()
        output_file = raw_data_dir / "guild_source.csv"
        
        # Download the file
        download_file(url, output_file)
        
        # Validate the downloaded file
        validate_guild_source(output_file)
        
        # Compute hash
        file_hash = compute_sha256(output_file)
        logger.info(f"File hash (SHA-256): {file_hash}")
        
        # Update metadata with provenance
        if 'sources' not in metadata:
            metadata['sources'] = {}
        
        metadata['sources']['guild'] = {
            'url': url,
            'local_path': str(output_file.relative_to(get_project_root())),
            'sha256': file_hash,
            'source_citation': EXPECTED_CITATION,
            'extraction_date': datetime.utcnow().isoformat(),
            'format': output_file.suffix.lower()
        }
        
        # Save updated metadata
        metadata_path = get_metadata_file()
        save_metadata(metadata, metadata_path)
        
        logger.info("Guild source download and validation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Guild source download failed: {e}")
        # Re-raise to ensure the pipeline fails loudly
        raise

if __name__ == "__main__":
    sys.exit(main())
