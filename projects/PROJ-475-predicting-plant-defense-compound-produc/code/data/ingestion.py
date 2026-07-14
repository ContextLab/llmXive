"""
Data ingestion module for plant defense compound prediction pipeline.
Fetches genomic, environmental, and compound data from verified URLs or generates mock data.
"""
import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError
from data.mock_generator import generate_all_mock_data

logger = get_module_logger(__name__)

def fetch_genomic_vcf(config: Dict[str, Any]) -> Optional[Path]:
    """
    Fetch genomic VCF data from verified NCBI SRA URL.
    
    Args:
        config: Configuration dictionary with verified URLs.
        
    Returns:
        Path to downloaded JSON file, or None if failed.
    """
    url = config.get('verified_urls', {}).get('genomic')
    if not url:
        logger.warning("No verified genomic URL found.")
        return None
    
    try:
        logger.info(f"Fetching genomic data from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save as JSON
        output_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'genomic_vcf.json'
        
        # Assuming response is JSON; if not, parse accordingly
        data = response.json()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Genomic data saved to {output_path}")
        check_disk_space(output_path.stat().st_size)
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch genomic data: {e}")
        return None

def fetch_environmental_metadata(config: Dict[str, Any]) -> Optional[Path]:
    """
    Fetch environmental metadata from verified WorldClim/GBIF URL.
    
    Args:
        config: Configuration dictionary with verified URLs.
        
    Returns:
        Path to downloaded JSON file, or None if failed.
    """
    url = config.get('verified_urls', {}).get('env')
    if not url:
        logger.warning("No verified environmental URL found.")
        return None
    
    try:
        logger.info(f"Fetching environmental data from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        output_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'env_data.json'
        
        data = response.json()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Environmental data saved to {output_path}")
        check_disk_space(output_path.stat().st_size)
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch environmental data: {e}")
        return None

def fetch_compound_profiles(config: Dict[str, Any]) -> Optional[Path]:
    """
    Fetch defense compound profiles from verified ChemBank/PhenolExplorer URL.
    
    Args:
        config: Configuration dictionary with verified URLs.
        
    Returns:
        Path to downloaded JSON file, or None if failed.
    """
    url = config.get('verified_urls', {}).get('compound')
    if not url:
        logger.warning("No verified compound URL found.")
        return None
    
    try:
        logger.info(f"Fetching compound data from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        output_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'compound_data.json'
        
        data = response.json()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Compound data saved to {output_path}")
        check_disk_space(output_path.stat().st_size)
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch compound data: {e}")
        return None

def generate_compound_data_via_mock(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Generate all mock data (genomic, environmental, compound) deterministically.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        Dictionary mapping data types to output paths.
    """
    logger.info("Generating deterministic mock data...")
    return generate_all_mock_data(config)

def run_ingestion_pipeline(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Run the full ingestion pipeline: fetch or generate all data sources.
    
    Args:
        config: Optional configuration dictionary.
        
    Returns:
        0 on success, non-zero on failure.
    """
    if config is None:
        config = get_config()
    
    try:
        logger.info("Starting data ingestion pipeline...")
        
        # Try to fetch real data
        genomic_path = fetch_genomic_vcf(config)
        env_path = fetch_environmental_metadata(config)
        compound_path = fetch_compound_profiles(config)
        
        # If any fetch failed, generate mock data
        if not all([genomic_path, env_path, compound_path]):
            logger.warning("Real data fetch failed or incomplete. Falling back to mock data.")
            mock_paths = generate_compound_data_via_mock(config)
            genomic_path = mock_paths.get('genomic')
            env_path = mock_paths.get('env')
            compound_path = mock_paths.get('compound')
        
        # Verify all paths exist
        if not all([genomic_path, env_path, compound_path]):
            logger.error("Ingestion failed: Could not obtain any data.")
            return 1
        
        logger.info("Ingestion pipeline completed successfully.")
        return 0
        
    except DiskSpaceError as e:
        logger.error(f"Ingestion failed due to disk space: {e}")
        return 2
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main(*args, **kwargs) -> int:
    """
    Main entry point for ingestion module.
    """
    from utils.logging import configure_root_logger
    configure_root_logger()
    
    config = get_config()
    if args and isinstance(args[0], dict):
        config = args[0]
    elif 'config' in kwargs:
        config = kwargs['config']
    
    return run_ingestion_pipeline(config)

if __name__ == '__main__':
    sys.exit(main())
