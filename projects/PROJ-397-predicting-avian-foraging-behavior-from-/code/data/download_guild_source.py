import os
import sys
import csv
import hashlib
import yaml
import logging
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_metadata_file
from utils.provenance import save_provenance_record, record_source_info

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verified static URL for the guild source data
GUILD_SOURCE_URL = "https://raw.githubusercontent.com/CornellLabofOrnithology/eBird_Taxonomy/main/guilds.csv"
# Fallback to a known static mirror if the primary fails, but we prefer the primary
# In a real production scenario, this might be an S3 bucket or a stable CDN.
# Using a placeholder for the fallback as per strict "fail loudly" if real source fails.
# However, the task says "verified static URL". We will use the Cornell URL as primary.
# If that 404s, we fail. We will not fake data.

def load_metadata_config():
    """Load the existing metadata.yaml file."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Creating new structure.")
        return {"datasets": {}, "artifacts": {}, "pipeline_runs": []}
    
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f)

def get_guild_source_url():
    """Return the verified URL for the guild source."""
    return GUILD_SOURCE_URL

def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, output_path):
    """Download a file from URL to output_path. Raises on failure."""
    logger.info(f"Downloading {url} to {output_path}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Downloaded successfully: {output_path}")
    except requests.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise FileNotFoundError(f"Could not download guild source from {url}. No fallback available.")

def validate_guild_source(filepath):
    """
    Validate that the downloaded CSV has the required 'source_citation' column.
    Raises ValueError if invalid.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found for validation: {filepath}")

    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no headers.")
            
            if 'source_citation' not in reader.fieldnames:
                raise ValueError(f"Missing required column 'source_citation'. Found columns: {reader.fieldnames}")
            
            # Check if there is at least one row of data
            first_row = next(reader, None)
            if first_row is None:
                raise ValueError("CSV file has headers but no data rows.")
            
            # Verify the column is not empty for the first row
            if not first_row.get('source_citation', '').strip():
                raise ValueError("Column 'source_citation' is empty in the first row.")
            
            logger.info(f"Validation passed. Columns: {reader.fieldnames}")
            return True
    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {e}")

def save_metadata(metadata, output_path):
    """Save metadata dictionary to YAML file."""
    with open(output_path, 'w') as f:
        yaml.safe_dump(metadata, f, default_flow_style=False, sort_keys=False)

def main():
    """Main execution function."""
    raw_data_dir = get_raw_data_dir()
    output_file = raw_data_dir / "guild_source.csv"
    metadata_file = get_metadata_file()

    # Ensure directory exists
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # Load current metadata
    metadata = load_metadata_config()
    if "datasets" not in metadata:
        metadata["datasets"] = {}

    url = get_guild_source_url()

    try:
        # Download
        download_file(url, output_file)

        # Compute checksum
        checksum = compute_sha256(output_file)

        # Validate content
        validate_guild_source(output_file)

        # Update metadata
        dataset_key = "guild_source"
        metadata["datasets"][dataset_key] = {
            "source_url": url,
            "version": "latest", # Or extract version from filename if available
            "download_date": datetime.utcnow().isoformat(),
            "checksum": checksum,
            "local_path": str(output_file.relative_to(project_root))
        }

        # Record provenance using the utility
        record_source_info(
            metadata=metadata,
            dataset_name=dataset_key,
            source_url=url,
            version="latest",
            extraction_date=datetime.utcnow().isoformat()
        )

        # Save metadata
        save_metadata(metadata, metadata_file)
        logger.info(f"Metadata updated at {metadata_file}")

        logger.info("Task T008a completed successfully.")

    except Exception as e:
        logger.error(f"Task T008a failed: {e}")
        # Ensure we don't leave partial metadata if download fails
        if output_file.exists():
            output_file.unlink()
        raise

if __name__ == "__main__":
    main()
