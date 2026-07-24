"""
Retrieve pre-processed 16S rRNA feature tables and metadata from public repositories.

This script loads dataset configurations from data/config/dataset_ids.json,
validates them against the schema defined in T004, and downloads the data
to data/raw/.

It implements the "Data Gap" protocol: if validation fails or no real data
can be retrieved, it logs a CRITICAL DATA GAP error and exits immediately.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

# Import the validator created in T004
# Note: The API surface lists `code/validators.py` with `validate_dataset_config`
try:
    from validators import validate_dataset_config
except ImportError:
    # Fallback for direct execution if module resolution differs
    from code.validators import validate_dataset_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/retrieve_data.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "config" / "dataset_ids.json"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset-config.schema.yaml"

def download_from_zenodo(dataset_id: str, output_dir: Path) -> bool:
    """
    Download pre-processed 16S tables/metadata from Zenodo.
    
    Args:
        dataset_id: The Zenodo ID (e.g., '10.5281/zenodo.1234567')
        output_dir: Directory to save the downloaded files
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    logger.info(f"Attempting to download from Zenodo: {dataset_id}")
    
    # Zenodo API endpoint for latest version or specific version
    # We will try to fetch the metadata first to locate files
    zenodo_api_url = f"https://zenodo.org/api/records/{dataset_id.split('.')[-1]}"
    
    try:
        # Use urllib to avoid adding heavy dependencies if not already present
        import urllib.request
        import urllib.error
        
        # Fetch metadata
        req = urllib.request.Request(zenodo_api_url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            metadata = json.loads(response.read().decode('utf-8'))
        
        if 'files' not in metadata or not metadata['files']:
            logger.error(f"No files found in Zenodo record {dataset_id}")
            return False
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download files (assuming feature table and metadata)
        # We look for common file patterns
        downloaded_count = 0
        for file_entry in metadata['files']:
            file_name = file_entry.get('key', 'unknown')
            file_link = file_entry.get('links', {}).get('self', '')
            
            if not file_link:
                continue
                
            logger.info(f"Downloading {file_name}...")
            local_path = output_dir / file_name
            
            try:
                with urllib.request.urlopen(file_link, timeout=60) as dl_response:
                    with open(local_path, 'wb') as f:
                        f.write(dl_response.read())
                downloaded_count += 1
                logger.info(f"Successfully downloaded {file_name} ({local_path.stat().st_size} bytes)")
            except Exception as e:
                logger.warning(f"Failed to download {file_name}: {e}")
        
        if downloaded_count == 0:
            logger.error(f"Failed to download any files from Zenodo record {dataset_id}")
            return False
            
        return True
        
    except urllib.error.URLError as e:
        logger.error(f"Network error accessing Zenodo for {dataset_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading from Zenodo: {e}")
        return False

def download_from_ncbi_sra(dataset_id: str, output_dir: Path) -> bool:
    """
    Download pre-processed 16S tables/metadata from NCBI SRA.
    
    Note: NCBI SRA typically requires using the SRA Toolkit (prefetch/sratoolkit)
    for raw data. For pre-processed feature tables, we assume they are hosted
    in a public FTP location or via the SRA API if available.
    
    For this implementation, we simulate the check against a known public
    pre-processed data source pattern or fail if not directly accessible
    via simple HTTP.
    
    Args:
        dataset_id: The SRA BioProject ID (e.g., 'PRJNA555687')
        output_dir: Directory to save the downloaded files
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    logger.info(f"Attempting to download from NCBI SRA: {dataset_id}")
    
    # NCBI SRA BioProject summary URL
    ncbi_api_url = f"https://www.ncbi.nlm.nih.gov/bioproject/?term={dataset_id}&report=docsum&format=json"
    
    try:
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(ncbi_api_url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            metadata = json.loads(response.read().decode('utf-8'))
        
        if 'result' not in metadata or 'bioprojects' not in metadata['result']:
            logger.error(f"Invalid response from NCBI for {dataset_id}")
            return False
        
        # Check if we can find links to associated data (e.g., SRA runs)
        # For pre-processed feature tables, we might need to look for associated
        # BioSample or specific FTP links.
        
        # Since direct pre-processed feature tables are not always in the JSON summary,
        # we will attempt to construct a known FTP path or check for associated
        # SRA files that might contain processed data (rare, but possible).
        # If the dataset is known to have pre-processed data in a specific location
        # (e.g., a Zenodo mirror linked in the description), we would use that.
        
        # Fallback: Check if the dataset ID corresponds to a known public pre-processed
        # dataset hosted elsewhere (e.g., QIITA or a specific FTP).
        # For this script, we assume the user has provided a dataset ID that
        # *should* be resolvable. If we cannot find a direct link to a feature table,
        # we log a warning but do not fail immediately if the metadata exists.
        # However, per "Data Gap" protocol, we must ensure we have the *data*.
        
        # Let's try a common pattern for SRA pre-processed data if available via FTP
        # Example: ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/...
        # This is complex. For this task, we will assume the dataset ID provided
        # in config_ids.json is valid and has associated files we can fetch
        # via a known public repository link if the direct SRA API doesn't yield
        # the feature table.
        
        # If we are here, we have metadata, but maybe not the feature table.
        # We will attempt to download a placeholder or fail if no file link found.
        # To strictly follow "Real Data Only", if we cannot find the file link:
        
        logger.warning(f"Found metadata for {dataset_id} but no direct feature table link in SRA API.")
        logger.warning("In a real scenario, this would require fetching from an associated FTP or BioSample.")
        logger.warning("Attempting to fetch from a generic SRA FTP location for processed data...")
        
        # Attempt a generic FTP fetch (this might fail if the file structure is different)
        # This is a best-effort implementation for the "real data" requirement.
        # If the specific PRJNA555687 has a known processed location, it would be here.
        # Since we cannot hardcode a specific FTP path for every ID without a mapping,
        # we rely on the fact that T004 validated the source as NCBI_SRA.
        
        # If we cannot find a file, we must fail the "Data Gap" check.
        # We will try to download a manifest or index file first.
        ftp_base = f"https://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/SRP140/SRP140378/" # Example path structure
        
        # Since we can't guess the exact path, we will log the failure to find the specific file
        # and return False, triggering the Data Gap protocol.
        logger.error(f"Could not locate pre-processed feature table for {dataset_id} via standard API.")
        return False
        
    except urllib.error.URLError as e:
        logger.error(f"Network error accessing NCBI for {dataset_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading from NCBI SRA: {e}")
        return False

def process_dataset(dataset: Dict[str, Any], output_dir: Path) -> bool:
    """
    Process a single dataset entry from the configuration.
    
    Args:
        dataset: Dictionary containing dataset metadata
        output_dir: Base directory for raw data
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    dataset_id = dataset.get('id')
    source = dataset.get('source')
    
    if not dataset_id or not source:
        logger.error(f"Invalid dataset entry: missing id or source. Entry: {dataset}")
        return False
    
    source_dir = output_dir / source
    source_dir.mkdir(parents=True, exist_ok=True)
    
    success = False
    if source.lower() == 'zenodo':
        success = download_from_zenodo(dataset_id, source_dir)
    elif source.lower() == 'ncbi_sra':
        success = download_from_ncbi_sra(dataset_id, source_dir)
    else:
        logger.error(f"Unsupported data source: {source}")
        return False
    
    if success:
        logger.info(f"Successfully processed dataset {dataset_id} from {source}")
    else:
        logger.error(f"Failed to process dataset {dataset_id} from {source}")
    
    return success

def main():
    """Main entry point for data retrieval."""
    logger.info("Starting data retrieval process...")
    
    # 1. Check if config file exists
    if not CONFIG_PATH.exists():
        logger.error("CRITICAL DATA GAP: Configuration file not found at " + str(CONFIG_PATH))
        sys.exit(1)
    
    # 2. Validate configuration against schema (T004)
    logger.info(f"Validating configuration file: {CONFIG_PATH}")
    try:
        is_valid = validate_dataset_config(str(CONFIG_PATH))
        if not is_valid:
            logger.error("CRITICAL DATA GAP: Configuration validation failed.")
            sys.exit(1)
        logger.info("Configuration validation passed.")
    except Exception as e:
        logger.error(f"CRITICAL DATA GAP: Error during validation: {e}")
        sys.exit(1)
    
    # 3. Load configuration
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL DATA GAP: Malformed JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CRITICAL DATA GAP: Error reading config file: {e}")
        sys.exit(1)
    
    datasets = config.get('datasets', [])
    if not datasets:
        logger.error("CRITICAL DATA GAP: No datasets found in configuration.")
        sys.exit(1)
    
    logger.info(f"Found {len(datasets)} datasets to process.")
    
    # 4. Ensure raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 5. Process each dataset
    success_count = 0
    fail_count = 0
    
    for dataset in datasets:
        if process_dataset(dataset, RAW_DATA_DIR):
            success_count += 1
        else:
            fail_count += 1
    
    # 6. Final check: Did we get any data?
    if success_count == 0:
        logger.error("CRITICAL DATA GAP: No datasets were successfully downloaded.")
        logger.error("The pipeline cannot proceed without real data.")
        sys.exit(1)
    
    logger.info(f"Data retrieval completed. Success: {success_count}, Failed: {fail_count}")
    
    # 7. List downloaded files for verification
    downloaded_files = list(RAW_DATA_DIR.rglob('*'))
    downloaded_files = [f for f in downloaded_files if f.is_file()]
    logger.info(f"Downloaded {len(downloaded_files)} files to {RAW_DATA_DIR}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())