"""
Data loading module for fetching PPI networks and essentiality labels.
Implements caching for expensive API calls (T041).
"""
import os
import logging
import json
import time
import csv
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import requests
from urllib.parse import urljoin

from config import load_config, get_path, get_confidence_thresholds
from utils import setup_logging, exponential_backoff, compute_sha256
from caching import cache_result, clear_cache, profile_function

logger = logging.getLogger(__name__)

class DataLoadingError(Exception):
    """Custom exception for data loading errors."""
    pass

# Constants
STRING_API_BASE = "https://string-db.org/api"
DEG_FTP_URL = "ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/deg_essential_genes.csv"
CACHE_PREFIX_STRING = "string_ppi"
CACHE_PREFIX_DEG = "deg_essentiality"

@cache_result(CACHE_PREFIX_STRING, ttl=86400 * 7)
def fetch_string_network(organism: str, confidence_threshold: int = 700) -> Dict[str, Any]:
    """
    Fetch PPI network from STRING API for a given organism.
    
    Args:
        organism: Organism name (e.g., 'human', 'yeast')
        confidence_threshold: Minimum confidence score (0-1000)
    
    Returns:
        Dictionary containing network data (nodes, edges)
    
    Raises:
        DataLoadingError: If API request fails or returns invalid data
    """
    # Map organism names to STRING tax IDs
    organism_tax_map = {
        'human': '9606',
        'mouse': '10090',
        'zebrafish': '7955',
        'worm': '6239',
        'fly': '7227',
        'xenopus': '8355',
        'dog': '9615',
        'yeast': '4932',
        's_cerevisiae': '4932'
    }
    
    tax_id = organism_tax_map.get(organism.lower())
    if not tax_id:
        raise DataLoadingError(f"Unknown organism mapping for: {organism}")
    
    # Construct API URL
    url = f"{STRING_API_BASE}/textmapping/v3.1/"
    params = {
        'string_ids': tax_id,
        'species': tax_id,
        'required_score': confidence_threshold,
        'caller_identity': 'llmXive_pipeline'
    }
    
    logger.info(f"Fetching STRING network for {organism} (tax_id={tax_id}) with threshold {confidence_threshold}")
    
    try:
        response = exponential_backoff(
            requests.get,
            url,
            params=params,
            max_retries=3,
            backoff_factor=2.0
        )
        
        response.raise_for_status()
        
        # Parse TSV response
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            raise DataLoadingError(f"Empty or invalid response from STRING for {organism}")
        
        # Parse header
        header = lines[0].split('\t')
        
        # Parse data
        edges = []
        nodes = set()
        
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                protein1 = parts[0]
                protein2 = parts[1]
                combined_score = int(parts[-1]) if parts[-1].isdigit() else 0
                
                edges.append({
                    'source': protein1,
                    'target': protein2,
                    'score': combined_score
                })
                nodes.add(protein1)
                nodes.add(protein2)
        
        result = {
            'organism': organism,
            'tax_id': tax_id,
            'threshold': confidence_threshold,
            'nodes': list(nodes),
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'fetched_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Successfully fetched {len(edges)} edges and {len(nodes)} nodes for {organism}")
        return result
        
    except requests.RequestException as e:
        raise DataLoadingError(f"Failed to fetch STRING network for {organism}: {e}")
    except Exception as e:
        raise DataLoadingError(f"Error parsing STRING response for {organism}: {e}")

def load_local_network(organism: str, threshold: int, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load previously cached network data from local storage.
    
    Args:
        organism: Organism name
        threshold: Confidence threshold
        data_dir: Optional custom data directory
    
    Returns:
        Network data dictionary or None if not found
    """
    if data_dir is None:
        data_dir = get_path("data_processed")
    
    file_path = data_dir / f"string_network_{organism}_t{threshold}.json"
    
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load local network for {organism}: {e}")
    
    return None

@cache_result(CACHE_PREFIX_DEG, ttl=86400 * 7)
def fetch_essentiality_labels(organism: str) -> Dict[str, Any]:
    """
    Fetch gene essentiality labels from DEG database.
    
    Args:
        organism: Organism name (must match DEG naming convention)
    
    Returns:
        Dictionary mapping gene IDs to essentiality labels (0/1)
    
    Raises:
        DataLoadingError: If fetch fails or data is invalid
    """
    # Map organism names to DEG identifiers
    deg_organism_map = {
        'human': 'Homo sapiens',
        'mouse': 'Mus musculus',
        'zebrafish': 'Danio rerio',
        'worm': 'Caenorhabditis elegans',
        'fly': 'Drosophila melanogaster',
        'xenopus': 'Xenopus tropicalis',
        'dog': 'Canis lupus familiaris',
        'yeast': 'Saccharomyces cerevisiae',
        's_cerevisiae': 'Saccharomyces cerevisiae'
    }
    
    deg_name = deg_organism_map.get(organism.lower())
    if not deg_name:
        raise DataLoadingError(f"Unknown DEG mapping for organism: {organism}")
    
    logger.info(f"Fetching essentiality labels for {organism} (DEG: {deg_name})")
    
    try:
        # Use requests to fetch via FTP over HTTP wrapper or direct FTP
        # Note: For production, consider using ftplib or a more robust FTP client
        # Here we attempt to fetch via a known HTTP mirror or direct FTP
        
        # Attempt direct FTP fetch
        import ftplib
        
        ftp = ftplib.FTP('ftp.ncbi.nlm.nih.gov')
        ftp.login()
        
        # Navigate to file
        file_path = '/pub/microarray/deg/deg_essential_genes.csv'
        
        # Read file content
        file_content = io.BytesIO()
        ftp.retrbinary(f'RETR {file_path}', file_content.write)
        ftp.quit()
        
        file_content.seek(0)
        csv_content = file_content.read().decode('utf-8')
        
        # Parse CSV
        reader = csv.DictReader(csv_content.splitlines())
        
        essentiality_data = {}
        organism_genes = []
        essential_count = 0
        non_essential_count = 0
        
        for row in reader:
            # Check if row matches our organism
            if row.get('Organism', '').lower() == deg_name.lower():
                gene_id = row.get('Gene ID', row.get('Gene', ''))
                if not gene_id:
                    continue
                
                # Determine essentiality (1=essential, 0=non-essential)
                essentiality = row.get('Essential', '0')
                if essentiality.lower() in ['yes', 'true', '1', 'essential']:
                    label = 1
                    essential_count += 1
                else:
                    label = 0
                    non_essential_count += 1
                
                essentiality_data[gene_id] = label
                organism_genes.append(gene_id)
        
        result = {
            'organism': organism,
            'deg_name': deg_name,
            'genes': organism_genes,
            'labels': essentiality_data,
            'essential_count': essential_count,
            'non_essential_count': non_essential_count,
            'total_count': len(organism_genes),
            'fetched_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Successfully fetched {len(organism_genes)} genes for {organism} "
                   f"({essential_count} essential, {non_essential_count} non-essential)")
        return result
        
    except ftplib.all_errors as e:
        raise DataLoadingError(f"FTP error fetching DEG data for {organism}: {e}")
    except Exception as e:
        raise DataLoadingError(f"Error processing DEG data for {organism}: {e}")

def load_local_essentiality(organism: str, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load previously cached essentiality data from local storage.
    
    Args:
        organism: Organism name
        data_dir: Optional custom data directory
    
    Returns:
        Essentiality data dictionary or None if not found
    """
    if data_dir is None:
        data_dir = get_path("data_processed")
    
    file_path = data_dir / f"essentiality_{organism}.json"
    
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load local essentiality for {organism}: {e}")
    
    return None

def map_ids(string_data: Dict[str, Any], essentiality_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map gene IDs between STRING and DEG datasets.
    
    Args:
        string_data: STRING network data
        essentiality_data: DEG essentiality labels
    
    Returns:
        Mapped data with aligned gene IDs
    """
    string_genes = set(string_data.get('nodes', []))
    deg_genes = set(essentiality_data.get('genes', []))
    
    # Find intersection
    common_genes = string_genes & deg_genes
    
    # Filter edges to common genes
    filtered_edges = [
        edge for edge in string_data.get('edges', [])
        if edge['source'] in common_genes and edge['target'] in common_genes
    ]
    
    # Filter labels to common genes
    filtered_labels = {
        gene: label for gene, label in essentiality_data.get('labels', {}).items()
        if gene in common_genes
    }
    
    mapping_coverage = len(common_genes) / len(string_genes) * 100 if string_genes else 0
    
    logger.info(f"ID mapping coverage: {mapping_coverage:.2f}% "
               f"({len(common_genes)}/{len(string_genes)} genes)")
    
    return {
        'nodes': list(common_genes),
        'edges': filtered_edges,
        'labels': filtered_labels,
        'node_count': len(common_genes),
        'edge_count': len(filtered_edges),
        'mapping_coverage_percent': mapping_coverage
    }

def load_essentiality_for_all_organisms(organisms: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Load essentiality data for multiple organisms.
    
    Args:
        organisms: List of organism names
    
    Returns:
        Dictionary mapping organism names to essentiality data
    """
    results = {}
    for organism in organisms:
        try:
            results[organism] = fetch_essentiality_labels(organism)
        except DataLoadingError as e:
            logger.error(f"Failed to load essentiality for {organism}: {e}")
            results[organism] = None
    return results

def save_essentiality_data(data: Dict[str, Any], organism: str, data_dir: Optional[Path] = None) -> Path:
    """
    Save essentiality data to local storage.
    
    Args:
        data: Essentiality data dictionary
        organism: Organism name
        data_dir: Optional custom data directory
    
    Returns:
        Path to saved file
    """
    if data_dir is None:
        data_dir = get_path("data_processed")
    
    file_path = data_dir / f"essentiality_{organism}.json"
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved essentiality data to {file_path}")
    return file_path

def main():
    """CLI for data loading operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data loading utility")
    parser.add_argument("--organism", type=str, help="Organism to fetch data for")
    parser.add_argument("--threshold", type=int, default=700, help="STRING confidence threshold")
    parser.add_argument("--action", choices=["fetch", "cache_info", "clear"], 
                      default="fetch", help="Action to perform")
    parser.add_argument("--all", action="store_true", help="Process all configured organisms")
    
    args = parser.parse_args()
    
    setup_logging()
    config = load_config()
    
    if args.action == "clear":
        cleared = clear_cache()
        print(f"Cleared {cleared} cache entries")
        return
        
    if args.action == "cache_info":
        from caching import _load_manifest
        manifest = _load_manifest()
        print(f"Cache entries: {len(manifest.get('entries', {}))}")
        return
    
    organisms = [args.organism] if args.organism else []
    if args.all:
        from config import get_organisms
        organisms = get_organisms(config)
    
    if not organisms:
        parser.print_help()
        return
    
    for organism in organisms:
        print(f"\nProcessing {organism}...")
        
        # Fetch network
        try:
            network = fetch_string_network(organism, args.threshold)
            print(f"  Network: {network['node_count']} nodes, {network['edge_count']} edges")
        except DataLoadingError as e:
            print(f"  Network fetch failed: {e}")
            continue
        
        # Fetch essentiality
        try:
            essentiality = fetch_essentiality_labels(organism)
            print(f"  Essentiality: {essentiality['total_count']} genes")
        except DataLoadingError as e:
            print(f"  Essentiality fetch failed: {e}")
            continue
        
        # Map IDs
        mapped = map_ids(network, essentiality)
        print(f"  Mapped: {mapped['node_count']} genes, {mapped['edge_count']} edges")
        print(f"  Coverage: {mapped['mapping_coverage_percent']:.2f}%")

if __name__ == "__main__":
    main()
