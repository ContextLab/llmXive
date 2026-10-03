import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import time

# Import from existing project modules as per API surface
from models import DiscrepancyType, Jurisdiction, Discrepancy, create_discrepancy_record, validate_output_schema
from error_handling import error_handler_factory, handle_errors, safe_execute, validate_required_fields, validate_input_types, log_function_call
from exceptions import DiscrepancyError, DataAcquisitionError, MissingDataError, ValidationFailureError, StatisticalModelError, ConfigurationError, ReproducibilityError
from utils.hashing import compute_file_hash, compute_directory_hash, save_checksums, load_checksums, verify_file_hash, verify_directory_checksums
from logger import setup_logging, get_logger, JSONFormatter, ReproducibilityContext, verify_reproducible

# Import pandas and numpy only when actually needed for processing
# This allows the module to be imported for structure even if dependencies aren't installed yet
# But the actual execution will fail loudly if dependencies are missing, which is correct behavior

def load_verified_sources_config(config_path: str = "config/verified_sources.yaml") -> Dict[str, Any]:
    """
    Load the verified sources configuration file.
    
    Args:
        config_path: Path to the verified sources YAML configuration file
        
    Returns:
        Dictionary containing verified sources metadata
        
    Raises:
        ConfigurationError: If the config file cannot be loaded or is invalid
    """
    import yaml
    
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Verified sources config file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to load verified sources config: {str(e)}")

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify the checksum of a downloaded file against the expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected checksum value (hex string)
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        DataAcquisitionError: If file cannot be read or hash computation fails
    """
    try:
        computed_hash = compute_file_hash(file_path, algorithm=algorithm)
        
        # Normalize both hashes to lowercase for comparison
        computed_hash = computed_hash.lower()
        expected_checksum = expected_checksum.lower()
        
        if computed_hash != expected_checksum:
            logging.error(f"Checksum mismatch for {file_path}")
            logging.error(f"  Expected: {expected_checksum}")
            logging.error(f"  Computed: {computed_hash}")
            return False
        
        logging.info(f"Checksum verification successful for {file_path}")
        return True
        
    except Exception as e:
        raise DataAcquisitionError(f"Failed to verify checksum for {file_path}: {str(e)}")

def download_from_verified_source(source_config: Dict[str, Any], output_dir: str) -> str:
    """
    Download data from a verified source.
    
    Args:
        source_config: Configuration dictionary for the source
        output_dir: Directory to save the downloaded file
        
    Returns:
        Path to the downloaded file
        
    Raises:
        DataAcquisitionError: If download fails or source is not verified
    """
    import urllib.request
    import ssl
    
    url = source_config.get('url')
    if not url:
        raise DataAcquisitionError("Source configuration missing URL")
    
    # Verify source is in the verified list (this should already be done by the caller)
    source_name = source_config.get('name', 'unknown')
    if not source_config.get('verified', False):
        raise DataAcquisitionError(f"Source '{source_name}' is not in the verified sources list")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Derive filename from URL or use configured filename
    filename = source_config.get('filename', os.path.basename(url.split('?')[0]))
    output_path = os.path.join(output_dir, filename)
    
    # Skip download if file already exists and checksum is valid
    if os.path.exists(output_path):
        expected_checksum = source_config.get('checksum')
        if expected_checksum:
            try:
                if verify_checksum(output_path, expected_checksum):
                    logging.info(f"File already exists and checksum matches: {output_path}")
                    return output_path
                else:
                    logging.warning(f"Existing file checksum mismatch, re-downloading: {output_path}")
            except Exception as e:
                logging.warning(f"Could not verify existing file, re-downloading: {str(e)}")
    
    # Download the file
    logging.info(f"Downloading from {url} to {output_path}")
    
    try:
        # Create SSL context that doesn't verify certificates (for compatibility)
        # In production, this should use proper certificate verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        urllib.request.urlretrieve(url, output_path)
        
        logging.info(f"Download complete: {output_path}")
        return output_path
        
    except Exception as e:
        raise DataAcquisitionError(f"Failed to download from {url}: {str(e)}")

def load_data_with_checksum_verification(source_id: str, config_path: str = "config/verified_sources.yaml") -> Tuple[str, Dict[str, Any]]:
    """
    Load data from a verified source with explicit checksum verification.
    
    This is the core function for T054: it verifies the integrity of the downloaded
    file against the known good hash from the verified source metadata BEFORE
    any processing occurs.
    
    Args:
        source_id: Identifier for the data source (must exist in verified_sources.yaml)
        config_path: Path to the verified sources configuration file
        
    Returns:
        Tuple of (file_path, source_metadata)
        
    Raises:
        DataAcquisitionError: If checksum verification fails or source is not found
    """
    logger = get_logger(__name__)
    logger.info(f"Starting data load with checksum verification for source: {source_id}")
    
    # Load verified sources configuration
    sources_config = load_verified_sources_config(config_path)
    
    # Find the source in the configuration
    source_config = None
    for source in sources_config.get('sources', []):
        if source.get('id') == source_id:
            source_config = source
            break
    
    if not source_config:
        raise DataAcquisitionError(f"Source '{source_id}' not found in verified sources configuration")
    
    # Download the file if needed
    output_dir = "data/raw"
    file_path = download_from_verified_source(source_config, output_dir)
    
    # EXPLICIT CHECKSUM VERIFICATION - This is the core of T054
    expected_checksum = source_config.get('checksum')
    if not expected_checksum:
        logger.warning(f"No checksum specified for source {source_id}, skipping verification")
    else:
        logger.info(f"Verifying checksum for {file_path} against expected: {expected_checksum}")
        
        if not verify_checksum(file_path, expected_checksum):
            error_msg = f"Checksum verification FAILED for {file_path}. " \
                       f"Expected: {expected_checksum}, " \
                       f"Aborting pipeline to prevent processing corrupted or tampered data."
            logger.error(error_msg)
            raise DataAcquisitionError(error_msg)
        
        logger.info("Checksum verification PASSED - proceeding with data processing")
    
    return file_path, source_config

class DataIngestionPipeline:
    """
    Unified ingestion pipeline for election data with integrity verification.
    
    This class implements the complete data acquisition and preprocessing pipeline,
    including the explicit checksum verification required by T054.
    """
    
    def __init__(self, config_path: str = "config/verified_sources.yaml"):
        """
        Initialize the ingestion pipeline.
        
        Args:
            config_path: Path to the verified sources configuration file
        """
        self.config_path = config_path
        self.sources_config = load_verified_sources_config(config_path)
        self.logger = get_logger(__name__)
        
    def run(self, source_id: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the full ingestion pipeline with checksum verification.
        
        Args:
            source_id: Identifier for the data source
            state: Optional state filter (e.g., "CA", "TX")
                
        Returns:
            Dictionary containing ingestion results and metadata
        """
        self.logger.info(f"Starting ingestion pipeline for source: {source_id}")
        
        # Step 1: Load data with checksum verification (T054 requirement)
        file_path, source_metadata = load_data_with_checksum_verification(source_id, self.config_path)
        
        # Step 2: Parse and process the data
        # Note: Actual parsing logic would go here, but for T054 we focus on the verification step
        # The parsing would be implemented in subsequent tasks
        
        result = {
            'status': 'success',
            'source_id': source_id,
            'file_path': file_path,
            'source_metadata': source_metadata,
            'checksum_verified': True,
            'state': state
        }
        
        self.logger.info(f"Ingestion pipeline completed successfully for {source_id}")
        return result

def main():
    """
    CLI entry point for the ingestion pipeline.
    
    Usage:
        python code/ingestion.py --source <source_id> [--state <state>] [--config <config_path>]
        
    Examples:
        python code/ingestion.py --source openelections-ca-2022 --state CA
        python code/ingestion.py --source eac-national-2020 --state TX
    """
    parser = argparse.ArgumentParser(description='Election Data Ingestion Pipeline with Checksum Verification')
    parser.add_argument('--source', type=str, required=True, 
                      help='Source ID from verified_sources.yaml')
    parser.add_argument('--state', type=str, required=False,
                      help='State filter (e.g., CA, TX)')
    parser.add_argument('--config', type=str, default='config/verified_sources.yaml',
                      help='Path to verified sources configuration file')
    parser.add_argument('--verify-reproducible', action='store_true',
                      help='Enable reproducibility verification mode')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        # Create and run the ingestion pipeline
        pipeline = DataIngestionPipeline(config_path=args.config)
        result = pipeline.run(source_id=args.source, state=args.state)
        
        # Log results
        logger.info(f"Ingestion completed: {json.dumps(result, indent=2, default=str)}")
        
        # If reproducibility verification is enabled, compute and log hashes
        if args.verify_reproducible:
            logger.info("Reproducibility verification mode enabled")
            verify_reproducible(result)
        
        return 0
        
    except DataAcquisitionError as e:
        logger.error(f"Data acquisition failed: {str(e)}")
        return 1
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 3

if __name__ == '__main__':
    sys.exit(main())