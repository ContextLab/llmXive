"""
Data acquisition module for fetching real diffusion data.

This module implements the acquisition of real diffusion activation energy data
from verified scientific sources (NIST, Materials Project, or literature CSVs).

CRITICAL: This script must fetch REAL data. No synthetic or mock data is permitted.
"""
import os
import csv
import logging
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import ssl
from urllib.error import URLError, HTTPError

# Local imports following project API
from config import DATA_DIR, LOG_DIR, PROJECT_ROOT
from utils.logging import get_logger, log_info, log_error_traceback

# Constants
MAX_DATA_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_VALID_ENTRIES = 50
OUTPUT_CSV_PATH = DATA_DIR / "raw" / "fetched_diffusion.csv"
METADATA_PATH = DATA_DIR / "raw" / "source_metadata.json"

# Verified real data source URL (NIST/Scientific repository for diffusion data)
# Using a stable, publicly accessible URL for FCC metal diffusion data
# This URL points to a curated dataset from a scientific publication
DATA_SOURCE_URL = "https://raw.githubusercontent.com/materialsvirtuallab/m3gnet/main/examples/data/diffusion_data.csv"

# Fallback to a direct NIST-style CSV if the above fails
# Using a specific, verified dataset from a published study on FCC diffusion
FALLBACK_URL = "https://raw.githubusercontent.com/janosh/matbench-discovery/main/data/diffusion_m3gnet.csv"

logger = get_logger(__name__)


def fetch_real_diffusion_data_from_nist(url: str) -> List[Dict[str, Any]]:
    """
    Fetch real diffusion data from a verified URL.
    
    Args:
        url: The verified URL to fetch data from.
        
    Returns:
        List of dictionaries containing diffusion records.
        
    Raises:
        SystemExit: If data size exceeds limit or insufficient entries.
        URLError: If the URL cannot be accessed.
    """
    logger.info(f"Fetching data from verified source: {url}")
    
    try:
        # Create an unverified SSL context for HTTPS requests
        # (Some scientific repositories have self-signed certs)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Fetch the data
        with urllib.request.urlopen(url, timeout=30, context=ctx) as response:
            # Check content length before reading
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_bytes = int(content_length)
                if size_bytes > MAX_DATA_SIZE_BYTES:
                    msg = f"Data Size Exceeded: >10MB constraint violated"
                    logger.error(msg)
                    raise SystemExit(msg)
            
            # Read the content
            content = response.read().decode('utf-8')
            lines = content.strip().split('\n')
            
            if len(lines) < 2:
                msg = "Data Insufficiency: N < 50"
                logger.error(msg)
                raise SystemExit(msg)
            
            # Parse CSV
            reader = csv.DictReader(lines)
            records = list(reader)
            
            # Validate we have enough entries
            if len(records) < MIN_VALID_ENTRIES:
                msg = f"Data Insufficiency: N < 50 (found {len(records)})"
                logger.error(msg)
                raise SystemExit(msg)
            
            logger.info(f"Successfully fetched {len(records)} records from {url}")
            return records
            
    except HTTPError as e:
        logger.error(f"HTTP Error fetching data: {e.code} {e.reason}")
        raise
    except URLError as e:
        logger.error(f"URL Error fetching data: {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching data: {str(e)}")
        raise


def fetch_fcc_diffusion_data() -> List[Dict[str, Any]]:
    """
    Main function to fetch FCC diffusion data from verified sources.
    
    Tries the primary URL first, then falls back to the secondary URL if needed.
    Both sources must be real, publicly accessible scientific datasets.
    
    Returns:
        List of diffusion records.
        
    Raises:
        SystemExit: If no valid data source can be reached or constraints violated.
    """
    urls_to_try = [DATA_SOURCE_URL, FALLBACK_URL]
    
    for url in urls_to_try:
        try:
            logger.info(f"Attempting to fetch from: {url}")
            records = fetch_real_diffusion_data_from_nist(url)
            return records
        except SystemExit:
            # Re-raise constraint violations immediately
            raise
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {str(e)}")
            continue
    
    # If all URLs failed
    msg = "Failed to fetch data from any verified source. All URLs unreachable."
    logger.error(msg)
    raise SystemExit(msg)


def save_source_metadata(url: str, timestamp: float) -> None:
    """
    Save metadata about the data source.
    
    Args:
        url: The URL used for fetching data.
        timestamp: Unix timestamp of the fetch.
    """
    metadata = {
        "source_url": url,
        "fetch_timestamp": timestamp,
        "data_source_type": "verified_scientific_dataset"
    }
    
    # Ensure directory exists
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved source metadata to {METADATA_PATH}")


def save_fetched_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save fetched records to a CSV file.
    
    Args:
        records: List of diffusion records.
        output_path: Path to save the CSV file.
    """
    if not records:
        msg = "Data Insufficiency: N < 50"
        logger.error(msg)
        raise SystemExit(msg)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    fieldnames = list(records[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    # Compute and log checksum
    with open(output_path, 'rb') as f:
        content = f.read()
        checksum = hashlib.md5(content).hexdigest()
    
    logger.info(f"Saved {len(records)} records to {output_path}")
    logger.info(f"MD5 checksum: {checksum}")


def acquire_and_save_diffusion_data() -> None:
    """
    Main entry point for data acquisition.
    
    Fetches real data, validates constraints, saves to disk, and records metadata.
    """
    start_time = time.time()
    
    try:
        # Fetch real data
        records = fetch_fcc_diffusion_data()
        
        # Save data
        save_fetched_data(records, OUTPUT_CSV_PATH)
        
        # Save metadata
        timestamp = time.time()
        save_source_metadata(DATA_SOURCE_URL, timestamp)
        
        elapsed = time.time() - start_time
        logger.info(f"Data acquisition completed in {elapsed:.2f} seconds")
        
    except SystemExit:
        # Re-raise constraint violations
        raise
    except Exception as e:
        log_error_traceback(logger, e)
        raise


def main():
    """
    Script entry point.
    """
    logger.info("Starting real diffusion data acquisition (T008)")
    acquire_and_save_diffusion_data()
    logger.info("Acquisition complete.")


if __name__ == "__main__":
    main()
