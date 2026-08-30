import json
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
import yaml

from config import get_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/gquery/gquery.fcgi"
ENCODE_BASE_URL = "https://www.encodeproject.org/search/"
GEO_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ENCODE_LIMIT = 100  # Max results per query for ENCODE
GEO_MAX_RESULTS = 1000  # Max results per query for GEO

def load_verified_datasets() -> List[Dict[str, Any]]:
    """Load verified datasets from data/verified_datasets.yaml."""
    path = Path("data/verified_datasets.yaml")
    if not path.exists():
        logger.warning(f"Verified datasets file not found at {path}. Returning empty list.")
        return []
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('verified_datasets', [])
    except Exception as e:
        logger.error(f"Error loading verified datasets: {e}")
        return []

def save_verified_dataset(dataset: Dict[str, Any]) -> bool:
    """Append a new verified dataset to data/verified_datasets.yaml."""
    path = Path("data/verified_datasets.yaml")
    try:
        # Load existing
        existing = load_verified_datasets()
        # Check if accession already exists
        if any(d.get('accession') == dataset.get('accession') for d in existing):
            logger.warning(f"Dataset {dataset.get('accession')} already exists.")
            return False
        
        existing.append(dataset)
        
        # Write back
        with open(path, 'w') as f:
            yaml.dump({'verified_datasets': existing, 'last_updated': time.strftime("%Y-%m-%d")}, f)
        return True
    except Exception as e:
        logger.error(f"Error saving verified dataset: {e}")
        return False

def tokenize_title(title: str) -> List[str]:
    """Tokenize a title into lowercase words, removing punctuation."""
    if not title:
        return []
    # Remove punctuation and split
    words = re.sub(r'[^\w\s]', '', title.lower()).split()
    return words

def calculate_token_overlap(tokens1: List[str], tokens2: List[str]) -> float:
    """Calculate Jaccard-like overlap between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    set1 = set(tokens1)
    set2 = set(tokens2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    if union == 0:
        return 0.0
    return intersection / union

def validate_reference(accession: str, title: str, threshold: float = 0.7) -> bool:
    """
    Validate a dataset accession/title against verified_datasets.yaml.
    Returns True if the title has >= threshold overlap with any verified title.
    """
    verified = load_verified_datasets()
    if not verified:
        # If no verified datasets exist, we cannot validate, so return False
        # to prevent false positives, or True if we assume all are valid? 
        # Per spec: "performing title-token overlap check". If no reference, no match.
        return False
    
    title_tokens = tokenize_title(title)
    for v in verified:
        v_title = v.get('title', '')
        v_tokens = tokenize_title(v_title)
        if calculate_token_overlap(title_tokens, v_tokens) >= threshold:
            logger.info(f"Accession {accession} validated against '{v_title}'")
            return True
    logger.info(f"Accession {accession} failed validation (no overlap >= {threshold})")
    return False

def search_geo(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Search GEO for datasets matching the query terms.
    Returns a list of accession info dicts.
    """
    # Construct query string
    query = " AND ".join([f'"{term}"' for term in query_terms])
    # Add specific filters for multi-generational and methylation/RNA-seq
    # GEO search syntax: (term1) AND (term2)
    full_query = f'({query}) AND ("GSE" OR "GPL")'
    
    params = {
        'db': 'gds',
        'term': full_query,
        'retmax': GEO_MAX_RESULTS,
        'retmode': 'json',
        'usehistory': 'y'
    }
    
    results = []
    try:
        response = requests.get(GEO_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        id_list = data.get('ids', [])
        
        # Fetch details for each ID
        if not id_list:
            logger.info("No GEO IDs found for query.")
            return []

        # Fetch details in batches to avoid rate limits
        for i in range(0, len(id_list), 10):
            batch_ids = id_list[i:i+10]
            detail_params = {
                'db': 'gds',
                'id': ','.join(batch_ids),
                'retmode': 'json',
                'rettype': 'full'
            }
            detail_resp = requests.get(GEO_API_URL, params=detail_params, timeout=30)
            detail_resp.raise_for_status()
            detail_data = detail_resp.json()
            
            for item in detail_data.get('result', {}).values():
                if item.get('id') in batch_ids:
                    title = item.get('title', '')
                    accession = item.get('id', '')
                    # Check if it matches our keywords roughly (in case API filtering is loose)
                    if any(term.lower() in title.lower() for term in query_terms):
                        results.append({
                            'accession': accession,
                            'title': title,
                            'source': 'GEO',
                            'url': f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
                        })
            
            time.sleep(0.5) # Rate limit
            
    except Exception as e:
        logger.error(f"GEO search failed: {e}")
    
    return results

def search_encode(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Search ENCODE for datasets matching the query terms.
    Returns a list of accession info dicts.
    """
    # ENCODE uses a different search syntax, often JSON based or query params
    # We will use the search endpoint with a query string
    query = " ".join(query_terms)
    params = {
        'searchTerm': query,
        'type': 'Experiment',
        'limit': ENCODE_LIMIT,
        'frame': 'embedded',
        'status': 'released'
    }
    
    results = []
    try:
        response = requests.get(ENCODE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        items = data.get('@graph', [])
        for item in items:
            accession = item.get('accession', '')
            title = item.get('description', item.get('title', ''))
            # Check keywords
            if any(term.lower() in title.lower() for term in query_terms):
                results.append({
                    'accession': accession,
                    'title': title,
                    'source': 'ENCODE',
                    'url': f"https://www.encodeproject.org/{accession}/"
                })
                
    except Exception as e:
        logger.error(f"ENCODE search failed: {e}")
        
    return results

def validate_dataset(dataset: Dict[str, Any]) -> bool:
    """
    Perform additional validation on a dataset.
    Currently checks title overlap with verified datasets.
    """
    accession = dataset.get('accession')
    title = dataset.get('title')
    if not accession or not title:
        return False
    return validate_reference(accession, title)

def filter_by_organism(datasets: List[Dict[str, Any]], organisms: List[str]) -> List[Dict[str, Any]]:
    """Filter datasets by organism name."""
    # Simple string matching for now
    filtered = []
    for d in datasets:
        title = d.get('title', '').lower()
        for org in organisms:
            if org.lower() in title:
                filtered.append(d)
                break
    return filtered

def check_metadata_completeness(dataset: Dict[str, Any]) -> bool:
    """
    Check if dataset has necessary metadata fields.
    For this task, we assume the search results are metadata-complete enough
    if they have an accession and title. Real metadata checks would require
    fetching the full record.
    """
    return bool(dataset.get('accession') and dataset.get('title'))

def run_discovery(output_path: str = "output/discovery_results.json") -> Dict[str, Any]:
    """
    Main discovery logic.
    1. Define search terms.
    2. Query GEO and ENCODE.
    3. Filter by organism (mouse, C. elegans, Drosophila).
    4. Validate against verified datasets.
    5. Check metadata completeness.
    6. Write results to JSON.
    """
    search_terms = ["multi-generational", "methylation", "RNA-seq", "fluctuating"]
    target_organisms = ["mouse", "mus musculus", "c. elegans", "caenorhabditis elegans", "drosophila", "fruit fly"]
    
    logger.info("Starting discovery process...")
    logger.info(f"Search terms: {search_terms}")
    
    # Search
    geo_results = search_geo(search_terms)
    encode_results = search_encode(search_terms)
    
    all_candidates = geo_results + encode_results
    logger.info(f"Found {len(all_candidates)} candidate datasets.")
    
    # Filter by organism
    organism_filtered = filter_by_organism(all_candidates, target_organisms)
    logger.info(f"After organism filter: {len(organism_filtered)} datasets.")
    
    # Validate and check metadata
    valid_datasets = []
    for d in organism_filtered:
        if check_metadata_completeness(d):
            if validate_dataset(d):
                valid_datasets.append(d)
            else:
                logger.debug(f"Skipping {d.get('accession')} due to validation failure.")
        else:
            logger.debug(f"Skipping {d.get('accession')} due to incomplete metadata.")
    
    logger.info(f"Final valid datasets: {len(valid_datasets)}")
    
    # Prepare output
    output_data = {
        "search_terms": search_terms,
        "total_candidates": len(all_candidates),
        "organism_filtered_count": len(organism_filtered),
        "valid_datasets": valid_datasets,
        "count": len(valid_datasets)
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Discovery results written to {output_path}")
    
    return output_data

def main():
    """Entry point for the discovery script."""
    output_path = get_env("DISCOVERY_OUTPUT", "output/discovery_results.json")
    results = run_discovery(output_path)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
