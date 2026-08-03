"""
Data Ingestion Module.
Fetches environmental metadata from verified WorldClim/GBIF URLs.
Enforces real data constraint: fails loudly if fetch fails.
"""
import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np

from utils.logging import get_module_logger, configure_root_logger
from config import get_config
from data.mock_generator import generate_all_mock_data
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def fetch_url_content(url: str) -> Optional[str]:
    """Fetches content from a URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def parse_vcf_content(content: str) -> List[Dict]:
    """
    Parses VCF content into a list of dictionaries.
    For this project, we simulate parsing a simplified VCF structure.
    """
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
    except json.JSONDecodeError:
        pass
    return []

def save_data(data: Any, output_path: Path):
    """Saves data to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved data to {output_path}")
    # Check disk space after save
    try:
        check_disk_space(output_path.stat().st_size * 1.5)
    except DiskSpaceError:
        logger.error("Disk space insufficient after save.")
        raise

def fetch_genomic_data() -> Dict:
    """Fetches genomic data from verified URL or generates mock."""
    config = get_config()
    url = config.verified_urls.get('genomic')
    output_path = PROJECT_ROOT / "data" / "raw" / "genomic_vcf.json"

    if url:
        logger.info(f"Fetching genomic data from {url}")
        content = fetch_url_content(url)
        if content:
            data = parse_vcf_content(content)
            if data:
                save_data({'data': data}, output_path)
                return {'data': data}
    
    # Real data fetch failed or not configured.
    # Per strict constraints, we must not silently fallback to mock if the task
    # specifically requires real data. However, the task description says:
    # "fetch ... OR generate mock data ... explicitly enforce verified URL check before fallback".
    # Given the execution history flagged "synthetic/fake INPUT data not authorized",
    # we must ensure the config has a real URL. If not, we raise.
    # But the task T011 specifically asks for the logic: "If config.verified_urls['env'] exists... else call mock_generator".
    # To satisfy the "Real data only" constraint while implementing the task logic:
    # We will check the URL. If it exists, we fetch. If it fails, we raise.
    # If the URL does not exist in config, we raise an error indicating configuration is missing.
    # This prevents silent mock generation which was flagged as fabrication.
    raise RuntimeError(
        "Real genomic data fetch failed. Verified URL 'genomic' not found in config or fetch failed. "
        "Do not generate mock data for research artifacts."
    )

def fetch_env_data() -> Dict:
    """Fetches environmental metadata from verified WorldClim/GBIF URL.
    
    Logic:
    1. Check config for verified URL.
    2. If present, fetch.
    3. If fetch fails, raise RuntimeError (NO MOCK FALLBACK).
    4. If URL not present, raise ConfigurationError.
    """
    config = get_config()
    url = config.verified_urls.get('env')
    output_path = PROJECT_ROOT / "data" / "raw" / "env_data.json"

    if not url:
        raise RuntimeError(
            "Configuration error: Verified URL for 'env' (WorldClim/GBIF) is not set. "
            "Cannot generate mock data for research artifacts."
        )

    logger.info(f"Fetching environmental data from {url}")
    content = fetch_url_content(url)
    
    if not content:
        raise RuntimeError(
            f"Failed to fetch environmental data from {url}. "
            "Real data fetch failed. No mock fallback allowed."
        )

    try:
        data = json.loads(content)
        # Ensure we have a list or dict with data
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        elif not isinstance(data, list):
            # If it's a single object, wrap it or handle appropriately
            data = [data]
        
        save_data(data, output_path)
        return data
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Failed to parse environmental data from {url}. "
            "Response was not valid JSON."
        )

def fetch_compound_data() -> Dict:
    """Fetches compound data from verified URL.
    
    Logic: Same strict enforcement as fetch_env_data.
    """
    config = get_config()
    url = config.verified_urls.get('compound')
    output_path = PROJECT_ROOT / "data" / "raw" / "compound_data.json"

    if not url:
        raise RuntimeError(
            "Configuration error: Verified URL for 'compound' is not set. "
            "Cannot generate mock data for research artifacts."
        )

    logger.info(f"Fetching compound data from {url}")
    content = fetch_url_content(url)
    
    if not content:
        raise RuntimeError(
            f"Failed to fetch compound data from {url}. "
            "Real data fetch failed. No mock fallback allowed."
        )

    try:
        data = json.loads(content)
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        elif not isinstance(data, list):
            data = [data]
        
        save_data(data, output_path)
        return data
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Failed to parse compound data from {url}. "
            "Response was not valid JSON."
        )

def run_all_ingestion():
    """Runs all ingestion steps."""
    logger.info("Starting Data Ingestion")
    try:
        fetch_genomic_data()
        fetch_env_data()
        fetch_compound_data()
        logger.info("Ingestion complete.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

def main(*args, **kwargs):
    """Entry point for ingestion script."""
    configure_root_logger()
    run_all_ingestion()

if __name__ == "__main__":
    main()
