"""
Data loading module for fetching PPI networks and essentiality labels.

Handles API failures, local fallbacks, and ID mapping.
"""
import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class DataLoadingError(Exception):
    """Custom exception for data loading errors."""
    pass

def map_ids(
    string_ids: Set[str],
    ensembl_ids: Set[str],
    organism: str
) -> Dict[str, str]:
    """
    Map STRING gene IDs to Ensembl IDs using BioMart.
    
    Args:
        string_ids: Set of STRING gene identifiers.
        ensembl_ids: Set of Ensembl gene identifiers.
        organism: Organism name for BioMart query.
        
    Returns:
        Dictionary mapping STRING IDs to Ensembl IDs.
    """
    # In a real implementation, this would query BioMart
    # For now, we return an empty mapping and log a warning
    # if the mapping is incomplete
    
    overlap = string_ids & ensembl_ids
    if not overlap:
        logger.warning(f"No ID overlap for {organism}: {len(string_ids)} STRING IDs, "
                     f"{len(ensembl_ids)} Ensembl IDs. Skipping mapping.")
        return {}
    
    # Placeholder: In real code, this would do actual BioMart lookup
    mapping = {gid: gid for gid in overlap}
    coverage = len(mapping) / len(string_ids) * 100 if string_ids else 0
    logger.info(f"ID mapping coverage for {organism}: {coverage:.1f}% ({len(mapping)} / {len(string_ids)})")
    
    return mapping

def fetch_string_network(
    organism: str,
    confidence_threshold: int = 700,
    timeout: int = 30
) -> Optional[Dict[str, List[str]]]:
    """
    Fetch PPI network from STRING API.
    
    Args:
        organism: Organism name (e.g., '9606' for human).
        confidence_threshold: Minimum confidence score (0-1000).
        timeout: Request timeout in seconds.
        
    Returns:
        Adjacency list dictionary or None if fetch fails.
    """
    base_url = "https://string-db.org/api/json"
    # Note: Real implementation would use proper STRING API endpoints
    # This is a placeholder structure
    
    try:
        # Placeholder for actual API call
        # response = requests.get(url, params=params, timeout=timeout)
        # response.raise_for_status()
        # data = response.json()
        
        logger.warning(f"STRING API fetch for {organism} is not fully implemented. "
                     f"Returning None to trigger local fallback.")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch STRING network for {organism}: {e}")
        return None
    except Exception as e:
        raise DataLoadingError(f"Unexpected error fetching STRING network: {e}")

def load_local_network(organism: str, data_dir: Path) -> Optional[Dict[str, List[str]]]:
    """
    Load PPI network from local file.
    
    Args:
        organism: Organism name.
        data_dir: Directory containing local data files.
        
    Returns:
        Adjacency list dictionary or None if file not found.
    """
    filepath = data_dir / f"{organism}_ppi.json"
    
    if not filepath.exists():
        logger.warning(f"Local network file not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded local network for {organism} from {filepath}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load local network for {organism}: {e}")
        return None

def fetch_essentiality_labels(
    organism: str,
    timeout: int = 30
) -> Optional[Dict[str, int]]:
    """
    Fetch gene essentiality labels from DEG database.
    
    Args:
        organism: Organism name.
        timeout: Request timeout in seconds.
        
    Returns:
        Dictionary mapping gene IDs to essentiality labels (0/1) or None.
    """
    try:
        # Placeholder for actual API call
        # response = requests.get(url, params=params, timeout=timeout)
        # response.raise_for_status()
        
        logger.warning(f"DEG API fetch for {organism} is not fully implemented. "
                     f"Returning None to trigger local fallback.")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch essentiality labels for {organism}: {e}")
        return None
    except Exception as e:
        raise DataLoadingError(f"Unexpected error fetching essentiality labels: {e}")

def load_local_essentiality(organism: str, data_dir: Path) -> Optional[Dict[str, int]]:
    """
    Load essentiality labels from local file.
    
    Args:
        organism: Organism name.
        data_dir: Directory containing local data files.
        
    Returns:
        Dictionary mapping gene IDs to labels or None.
    """
    filepath = data_dir / f"{organism}_essentiality.json"
    
    if not filepath.exists():
        logger.warning(f"Local essentiality file not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded local essentiality for {organism} from {filepath}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load local essentiality for {organism}: {e}")
        return None

def load_essentiality_for_all_organisms(
    organisms: List[str],
    data_dir: Path
) -> Dict[str, Dict[str, int]]:
    """
    Load essentiality labels for multiple organisms.
    
    Args:
        organisms: List of organism names.
        data_dir: Directory containing local data files.
        
    Returns:
        Dictionary mapping organism names to their essentiality labels.
    """
    results = {}
    for organism in organisms:
        labels = load_local_essentiality(organism, data_dir)
        if labels:
            results[organism] = labels
        else:
            logger.warning(f"No essentiality data available for {organism}")
    
    return results

def save_essentiality_data(
    data: Dict[str, Dict[str, int]],
    output_dir: Path
) -> Path:
    """
    Save essentiality data to a JSON file.
    
    Args:
        data: Dictionary of organism data.
        output_dir: Output directory.
        
    Returns:
        Path to saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "essentiality_labels.json"
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved essentiality data to {filepath}")
    return filepath

def main():
    """Main entry point for data loading module."""
    import argparse
    from code.config import load_config, get_organisms, get_path
    
    parser = argparse.ArgumentParser(description='Load PPI networks and essentiality labels.')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    config = load_config(args.config)
    organisms = get_organisms(config)
    data_dir = Path(get_path(config, 'data_raw'))
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(level=logging.INFO)
    
    for organism in organisms:
        logger.info(f"Loading data for {organism}")
        
        # Try to fetch from API, fall back to local
        network = fetch_string_network(organism)
        if network is None:
            network = load_local_network(organism, data_dir)
        
        labels = fetch_essentiality_labels(organism)
        if labels is None:
            labels = load_local_essentiality(organism, data_dir)
        
        if network and labels:
            logger.info(f"Successfully loaded data for {organism}")
        else:
            logger.warning(f"Incomplete data for {organism}: network={network is not None}, labels={labels is not None}")

if __name__ == '__main__':
    main()
