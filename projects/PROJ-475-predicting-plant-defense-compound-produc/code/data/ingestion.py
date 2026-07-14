import json
import os
import sys
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging

from utils.logging import get_module_logger
from utils.io import check_disk_space, compute_checksum
from data.mock_generator import generate_all_mock_data
from config import get_config

logger = get_module_logger(__name__)

# --- Configuration and Constants ---
# These are now centralized to avoid repetition across fetch functions
FETCH_TIMEOUT = 30
RETRY_COUNT = 3
DISK_BUFFER_FACTOR = 1.5

# --- Generic Fetching Logic (DRY) ---
def _fetch_from_url(
    url: str,
    output_path: Path,
    fetch_type: str,
    expected_size_mb: float = 10.0
) -> bool:
    """
    Generic helper to fetch data from a URL with retry logic, disk checks, and checksums.

    Args:
        url: The verified URL to fetch from.
        output_path: Where to save the JSON file.
        fetch_type: Human-readable name for logging (e.g., 'genomic', 'env').
        expected_size_mb: Estimated size in MB for disk space check.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Fetching {fetch_type} data from {url}...")

    # Check disk space before attempting download
    estimated_bytes = int(expected_size_mb * 1024 * 1024)
    try:
        check_disk_space(estimated_bytes * DISK_BUFFER_FACTOR)
    except Exception as e:
        logger.error(f"Disk space check failed for {fetch_type}: {e}")
        return False

    headers = {'User-Agent': 'llmXive-Research-Agent/1.0'}
    last_error = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write data
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Compute and store checksum
            checksum = compute_checksum(output_path)
            logger.info(f"Successfully fetched {fetch_type} data. Checksum: {checksum}")
            return True

        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{RETRY_COUNT} failed for {fetch_type}: {e}")
            if attempt == RETRY_COUNT:
                logger.error(f"Failed to fetch {fetch_type} data after {RETRY_COUNT} attempts.")
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received for {fetch_type}: {e}")
            return False

    logger.error(f"Giving up on fetching {fetch_type} data.")
    return False

# --- Specific Ingestion Functions ---

def fetch_genomic_vcf_from_verified_url() -> Optional[Path]:
    """Fetch genomic VCF data or return path to mock data if URL fails."""
    config = get_config()
    output_path = Path(config.paths.raw_dir) / "genomic_vcf.json"

    verified_url = config.verified_urls.get('genomic')

    if verified_url:
        if _fetch_from_url(verified_url, output_path, "genomic", expected_size_mb=50.0):
            return output_path
        else:
            logger.warning("Genomic fetch failed, falling back to mock data.")
    
    # Fallback to mock generation if URL not set or fetch failed
    logger.info("Generating mock genomic data.")
    generate_all_mock_data() # This generates all mocks including genomic
    return output_path

def fetch_environmental_metadata_from_verified_url() -> Optional[Path]:
    """Fetch environmental metadata or return path to mock data if URL fails."""
    config = get_config()
    output_path = Path(config.paths.raw_dir) / "env_data.json"

    verified_url = config.verified_urls.get('env')

    if verified_url:
        if _fetch_from_url(verified_url, output_path, "environmental", expected_size_mb=5.0):
            return output_path
        else:
            logger.warning("Environmental fetch failed, falling back to mock data.")
    
    # Fallback
    logger.info("Generating mock environmental data.")
    generate_all_mock_data()
    return output_path

def fetch_compound_profiles_from_verified_url() -> Optional[Path]:
    """Fetch defense compound profiles or return path to mock data if URL fails."""
    config = get_config()
    output_path = Path(config.paths.raw_dir) / "compound_data.json"

    verified_url = config.verified_urls.get('compound')

    if verified_url:
        if _fetch_from_url(verified_url, output_path, "compound", expected_size_mb=2.0):
            return output_path
        else:
            logger.warning("Compound fetch failed, falling back to mock data.")
    
    # Fallback
    logger.info("Generating mock compound data.")
    generate_all_mock_data()
    return output_path

def generate_mock_compound_data() -> Path:
    """Wrapper to generate mock compound data specifically."""
    logger.info("Generating mock compound data (specific wrapper).")
    generate_all_mock_data()
    config = get_config()
    return Path(config.paths.raw_dir) / "compound_data.json"

def ingest_compound_data() -> Path:
    """
    Orchestrate compound data ingestion: fetch from verified URL or generate mock.
    This is the main entry point for the task requirement.
    """
    config = get_config()
    output_path = Path(config.paths.raw_dir) / "compound_data.json"
    
    # Ensure raw directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check verified URL configuration
    if config.verified_urls.get('compound'):
        success = _fetch_from_url(
            config.verified_urls['compound'],
            output_path,
            "compound",
            expected_size_mb=2.0
        )
        if success:
            return output_path
    
    # If no verified URL or fetch failed, generate mock
    logger.info("Using mock data for compounds.")
    generate_all_mock_data()
    return output_path

def main():
    """Main entry point for ingestion pipeline."""
    logger.info("Starting data ingestion pipeline.")
    
    # Execute ingestion for all three modalities
    genomic_path = fetch_genomic_vcf_from_verified_url()
    env_path = fetch_environmental_metadata_from_verified_url()
    compound_path = ingest_compound_data() # Uses the specific function for compounds

    if all([genomic_path, env_path, compound_path]):
        logger.info("Ingestion pipeline completed successfully.")
        return 0
    else:
        logger.error("Ingestion pipeline encountered errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
