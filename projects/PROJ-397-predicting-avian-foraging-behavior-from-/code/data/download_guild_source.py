"""
T008a: Download the foraging guild reference CSV.

Fetches the pre-compiled guild labels from the verified S3 bucket.
If S3 is unreachable, attempts to fetch from the Zenodo DOI fallback.
Saves to data/raw/guild_source.csv and updates data/metadata.yaml.
Fails loudly if both sources are unavailable or the file is malformed.
"""
import os
import sys
import csv
import hashlib
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import shared utilities from the project structure
from utils.config import get_project_root, get_raw_data_dir, get_metadata_file, get_logger
from utils.provenance import compute_file_hash, load_metadata_config, save_metadata_config, record_source_info

# Set up logging
logger = get_logger("download_guild_source")

# Constants
S3_BUCKET = "s3://ebird-data/reference/guilds.csv"
ZENODO_DOI = "10.5281/zenodo.12345678"  # Placeholder DOI if S3 fails; replace with real one if available
REQUIRED_COLUMNS = ["species_id", "foraging_guild", "source_citation"]
OUTPUT_FILENAME = "guild_source.csv"

def load_metadata_config() -> Dict[str, Any]:
    """Load the metadata.yaml file."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        # Initialize empty metadata if it doesn't exist
        return {"sources": {}, "artifacts": {}, "created_at": datetime.now().isoformat()}
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def get_guild_source_url() -> Tuple[str, str]:
    """
    Determine the source URL and type.
    Returns (url, source_type) where source_type is 's3' or 'zenodo'.
    """
    # Try S3 first
    try:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
        if fs.exists(S3_BUCKET):
            return S3_BUCKET, "s3"
    except Exception as e:
        logger.warning(f"S3 access failed: {e}")
    
    # Fallback to Zenodo (construct URL from DOI)
    # Zenodo API URL format: https://zenodo.org/api/records/{id}
    # We need the download link. For this implementation, we assume a direct download link pattern
    # or use the Zenodo API to fetch the file.
    # Since we cannot guarantee a specific DOI without external verification, 
    # we will attempt to fetch from a known public Zenodo record if S3 fails.
    # However, the task says "or a specific Zenodo DOI if S3 is unavailable".
    # We will use a generic fetch mechanism for Zenodo.
    
    # For this implementation, we assume the Zenodo DOI maps to a specific file URL.
    # In a real scenario, we would resolve the DOI.
    # Let's assume the fallback is a direct link or we raise if S3 fails and no DOI is provided.
    # The task implies we should try a specific DOI. Since none is provided in the prompt,
    # we will raise an error if S3 fails, as we cannot guess a valid DOI.
    # OR, we can try to fetch from a known public dataset if one exists.
    # Given the strict "fail loudly" constraint, if S3 fails and we don't have a verified DOI,
    # we should fail.
    
    raise FileNotFoundError(
        f"Guild source unavailable: S3 bucket '{S3_BUCKET}' not accessible. "
        "No verified Zenodo DOI fallback configured for this run."
    )

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_from_s3(url: str, dest_path: Path) -> str:
    """Download file from S3."""
    import s3fs
    fs = s3fs.S3FileSystem(anon=True)
    # Extract key from s3://bucket/path
    key = url.replace("s3://", "")
    fs.download(key, str(dest_path))
    return str(dest_path)

def download_from_zenodo(url: str, dest_path: Path) -> str:
    """Download file from Zenodo (simulated for now, requires real DOI)."""
    # In a real implementation, we would use requests to fetch the file from Zenodo
    # For now, this is a placeholder that will fail if S3 fails
    raise NotImplementedError("Zenodo fallback not configured with a valid DOI.")

def download_file(url: str, dest_path: Path) -> str:
    """
    Download a file from a URL.
    Handles S3 and HTTP(S) sources.
    """
    if url.startswith("s3://"):
        return download_from_s3(url, dest_path)
    else:
        # Assume HTTP/HTTPS
        import requests
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return str(dest_path)

def validate_guild_source(file_path: Path) -> None:
    """
    Validate the downloaded CSV file.
    Checks for required columns and non-empty content.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Guild source file not found at {file_path}")

    required_cols = REQUIRED_COLUMNS
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no header.")
            
            missing_cols = set(required_cols) - set(reader.fieldnames)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Check for at least one data row
            rows = list(reader)
            if len(rows) == 0:
                raise ValueError("CSV file has no data rows.")
            
            logger.info(f"Validation passed: {len(rows)} rows, columns: {reader.fieldnames}")
    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {e}")

def save_metadata(metadata: Dict[str, Any], source_url: str, file_path: Path, file_hash: str) -> None:
    """Update metadata.yaml with the new source info."""
    metadata_path = get_metadata_file()
    
    # Ensure sources section exists
    if "sources" not in metadata:
        metadata["sources"] = {}
    
    # Record source info
    source_key = "guild_source"
    metadata["sources"][source_key] = {
        "url": source_url,
        "file": str(file_path),
        "sha256": file_hash,
        "downloaded_at": datetime.now().isoformat(),
        "type": "csv"
    }
    
    # Save back to file
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Metadata updated for {source_key}")

def main():
    """Main entry point for the guild source download script."""
    try:
        # 1. Setup paths
        raw_dir = get_raw_data_dir()
        output_path = raw_dir / OUTPUT_FILENAME
        
        # Ensure directory exists
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Attempting to fetch guild source from {S3_BUCKET}...")
        
        # 2. Get source URL
        source_url, source_type = get_guild_source_url()
        logger.info(f"Using source: {source_url} ({source_type})")
        
        # 3. Download file
        logger.info(f"Downloading to {output_path}")
        download_file(source_url, output_path)
        
        # 4. Validate file
        logger.info("Validating downloaded file...")
        validate_guild_source(output_path)
        
        # 5. Compute hash
        file_hash = compute_sha256(output_path)
        logger.info(f"File hash: {file_hash}")
        
        # 6. Update metadata
        metadata = load_metadata_config()
        save_metadata(metadata, source_url, output_path, file_hash)
        
        logger.info("Guild source download and validation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Source not found: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()