import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Configure logging for the data ingestion pipeline
# This ensures that cell type counts, download status, and exclusion reasons are captured
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("ctcf_ingest")
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Load the manifest JSON file containing verified data sources.
    Returns a list of dictionaries with experiment details.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'entries' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'entries' in data:
        return data['entries']
    else:
        raise ValueError("Manifest file must be a list or contain an 'entries' key")

def download_file(url: str, dest_path: Path, timeout: int = 300) -> bool:
    """
    Download a file from a URL to a destination path.
    Returns True if successful, False otherwise.
    """
    try:
        logging.info(f"Downloading from {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"Successfully downloaded {dest_path.name}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {str(e)}")
        return False

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_manifest_entry(
    entry: Dict[str, Any], 
    data_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Process a single manifest entry: download file, calculate checksum, update entry.
    Returns updated entry with download status, checksum, and local path.
    """
    cell_type = entry.get('cell_type', 'unknown')
    file_type = entry.get('file_type', 'unknown')
    accession_id = entry.get('accession_id', 'unknown')
    url = entry.get('url')
    
    if not url:
        logger.warning(f"Skipping {cell_type} {file_type}: No URL provided")
        return {
            **entry,
            'status': 'skipped',
            'reason': 'missing_url'
        }
    
    # Determine local path
    filename = f"{accession_id}_{file_type}"
    local_path = data_dir / filename
    
    # Download file
    success = download_file(url, local_path)
    
    if success:
        checksum = calculate_sha256(local_path)
        logger.info(f"Downloaded {cell_type} {file_type}: {local_path.name} (SHA256: {checksum[:16]}...)")
        
        return {
            **entry,
            'status': 'downloaded',
            'local_path': str(local_path),
            'checksum': checksum
        }
    else:
        logger.error(f"Failed to download {cell_type} {file_type}: {accession_id}")
        return {
            **entry,
            'status': 'failed',
            'reason': 'download_error'
        }

def main():
    """
    Main function to execute data ingestion with comprehensive logging.
    
    This function:
    1. Loads the manifest of verified data sources
    2. Logs initial counts of cell types and data types
    3. Downloads each file and logs progress
    4. Tracks and logs exclusion reasons for any failures
    5. Generates a summary report of the ingestion process
    """
    logger = setup_logging()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "data" / "manifest.json"
    data_dir = project_root / "data" / "raw"
    
    logger.info("=" * 60)
    logger.info("Starting CTCF Data Ingestion Pipeline")
    logger.info("=" * 60)
    
    # Load manifest
    try:
        manifest = load_manifest(manifest_path)
        logger.info(f"Loaded manifest with {len(manifest)} entries")
    except Exception as e:
        logger.error(f"Failed to load manifest: {str(e)}")
        sys.exit(1)
    
    # Log initial statistics
    cell_types = set()
    file_types = set()
    for entry in manifest:
        if entry.get('cell_type'):
            cell_types.add(entry['cell_type'])
        if entry.get('file_type'):
            file_types.add(entry['file_type'])
    
    logger.info(f"Found {len(cell_types)} unique cell types: {', '.join(sorted(cell_types))}")
    logger.info(f"Found {len(file_types)} unique file types: {', '.join(sorted(file_types))}")
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each entry
    results = []
    successful_downloads = 0
    failed_downloads = 0
    skipped_entries = 0
    
    exclusion_reasons = {}
    
    for idx, entry in enumerate(manifest, 1):
        cell_type = entry.get('cell_type', 'unknown')
        file_type = entry.get('file_type', 'unknown')
        accession_id = entry.get('accession_id', 'unknown')
        
        logger.info(f"[{idx}/{len(manifest)}] Processing: {cell_type} - {file_type} - {accession_id}")
        
        result = process_manifest_entry(entry, data_dir, logger)
        results.append(result)
        
        status = result.get('status', 'unknown')
        
        if status == 'downloaded':
            successful_downloads += 1
        elif status == 'failed':
            failed_downloads += 1
            reason = result.get('reason', 'unknown')
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            logger.warning(f"Excluded {cell_type} {file_type}: {reason}")
        elif status == 'skipped':
            skipped_entries += 1
            reason = result.get('reason', 'unknown')
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            logger.info(f"Skipped {cell_type} {file_type}: {reason}")
    
    # Log summary statistics
    logger.info("=" * 60)
    logger.info("Ingestion Summary")
    logger.info("=" * 60)
    logger.info(f"Total entries processed: {len(manifest)}")
    logger.info(f"Successful downloads: {successful_downloads}")
    logger.info(f"Failed downloads: {failed_downloads}")
    logger.info(f"Skipped entries: {skipped_entries}")
    
    if exclusion_reasons:
        logger.info("Exclusion reasons:")
        for reason, count in exclusion_reasons.items():
            logger.info(f"  - {reason}: {count}")
    
    # Save updated manifest
    output_manifest_path = project_root / "data" / "manifest_processed.json"
    with open(output_manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Updated manifest saved to: {output_manifest_path}")
    logger.info("Data ingestion pipeline completed successfully")
    
    # Exit with error code if any downloads failed
    if failed_downloads > 0:
        logger.warning(f"Some downloads failed ({failed_downloads}). Review logs for details.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()