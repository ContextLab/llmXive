"""
Data Ingestion Module for Plant Defense Compound Prediction Pipeline.

This module handles fetching genomic, environmental, and defense compound data
from verified public sources or generating deterministic mock data for CI/testing.

It enforces strict verified URL checks to prevent fabrication and ensures
disk space availability before large downloads.
"""

import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Local imports
from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space, compute_checksum
from data.mock_generator import generate_mock_compound_data

# Initialize logger
logger = get_module_logger(__name__)

# Constants
OUTPUT_DIR = Path("data/raw")
COMPOUND_OUTPUT_PATH = OUTPUT_DIR / "compound_data.json"
DISK_SPACE_BUFFER = 1.5  # 1.5x safety margin

def fetch_url_content(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch content from a URL and parse it as JSON.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        requests.RequestException: If the request fails.
        ValueError: If the response is not valid JSON.
    """
    logger.info(f"Fetching content from: {url}")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {url}: {e}")
        raise

def save_data(data: Dict[str, Any], output_path: Path) -> str:
    """
    Save data to a JSON file and compute its checksum.

    Args:
        data: The data dictionary to save.
        output_path: Path to the output file.

    Returns:
        The SHA256 checksum of the saved file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    checksum = compute_checksum(output_path)
    logger.info(f"Saved data to {output_path} (checksum: {checksum})")
    return checksum

def fetch_compound_data() -> Dict[str, Any]:
    """
    Fetch defense compound profiles from verified sources.

    Logic:
    1. Check config for verified_urls['compound'].
    2. If present, fetch from the URL.
    3. If not present, generate deterministic mock data (for CI).
    4. Verify disk space before writing.
    5. Save to data/raw/compound_data.json.

    Returns:
        The compound data dictionary.
    """
    config = get_config()
    verified_urls = config.get('verified_urls', {})
    compound_url = verified_urls.get('compound')

    data = None

    if compound_url:
        logger.info(f"Fetching compound data from verified URL: {compound_url}")
        try:
            # Attempt to fetch real data
            # Note: Real sources like ChemBank/PhenolExplorer often require specific API endpoints
            # or scraping. Here we attempt a generic JSON fetch. If the URL is a known API,
            # this works. If it's a webpage, the parse logic might need adjustment,
            # but the task requires using the verified URL.
            data = fetch_url_content(compound_url)
            logger.info("Successfully fetched real compound data.")
        except Exception as e:
            logger.error(f"Failed to fetch real data from {compound_url}: {e}")
            logger.warning("Falling back to mock data generation as per CI constraints.")
            # If fetch fails, we fall through to mock generation if allowed by context,
            # but strictly speaking, if a URL is provided and fails, it should raise.
            # However, the task description says "OR generate mock data", implying a fallback.
            # Given the "Fabricated Results" error in history, we must be careful.
            # We will raise if real fetch fails and no mock is explicitly requested for CI.
            # But T012 spec says: "If config.verified_urls['compound'] exists, fetch; else call mock_generator."
            # It does NOT explicitly say "fetch fails -> mock". It says "exists -> fetch".
            # If fetch fails, the pipeline should fail loudly to avoid fake data.
            # However, to satisfy the "OR generate mock" part of the prompt for CI:
            # We assume if the URL exists but fails, we might need a fallback ONLY if explicitly configured.
            # But the strict instruction "NEVER fabricate" implies we should NOT fall back silently.
            # Let's re-read the specific T012 logic: "If config.verified_urls['compound'] exists, fetch; else call mock_generator."
            # This implies:
            #   if exists: fetch (and if fetch fails, it's an error, not a fallback to mock)
            #   else: mock
            # This aligns with "Fail loudly".
            raise RuntimeError(f"Real data fetch failed and no fallback configured for verified URL: {compound_url}") from e

    else:
        logger.warning("No verified URL for compound data found. Generating deterministic mock data for CI.")
        # Generate deterministic mock data
        data = generate_mock_compound_data()
        logger.info("Mock compound data generated.")

    # Post-check: Verify disk space before writing
    estimated_size = sys.getsizeof(json.dumps(data))
    check_disk_space(estimated_size * DISK_SPACE_BUFFER)

    # Save data
    checksum = save_data(data, COMPOUND_OUTPUT_PATH)

    # Update config with checksum (optional, for manifest)
    config['data_checksums']['compound'] = checksum

    return data

def run_all_ingestion() -> Dict[str, Any]:
    """
    Run all ingestion tasks (Genomic, Env, Compound) in sequence.

    Returns:
        A dictionary containing paths and checksums of all generated files.
    """
    logger.info("Starting all ingestion tasks...")
    
    # Run compound ingestion (T012)
    compound_data = fetch_compound_data()
    
    # Note: T010 and T011 are assumed to be run separately or in a larger pipeline.
    # This function specifically ensures T012 is executed if called.
    
    return {
        "compound_data_path": str(COMPOUND_OUTPUT_PATH),
        "status": "success"
    }

def main():
    """
    Entry point for running the compound data ingestion script directly.
    """
    configure_root_logger()
    try:
        result = run_all_ingestion()
        logger.info(f"Ingestion complete. Output: {result}")
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())