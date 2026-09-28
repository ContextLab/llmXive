"""
Literature Extraction Pipeline (T040a).

This script fetches and parses real literature data from PubMed/PMC
to extract effect sizes (correlation coefficients) for the relationship
between gut microbiome and cognitive flexibility.

Source: PubMed API
Output: data/raw/literature_metadata.json

Note: This implementation uses a verified real data source (PubMed) and
does NOT fall back to synthetic data. If the API fails, it raises an error.
"""
import os
import sys
import json
import logging
import time
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import get_data_raw_path, setup_logger

# Configure logging
logger = setup_logger("literature_extraction")

# PubMed API configuration
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = "llmXive-researcher@example.com"  # Required by NCBI
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0

def get_project_root():
    return project_root

def get_data_raw():
    return get_data_raw_path()

def search_pubmed_ids(query, max_results=50):
    """
    Search PubMed for relevant articles and return PMIDs.
    
    Args:
        query (str): Search query string.
        max_results (int): Maximum number of results to return.
        
    Returns:
        list: List of PMID strings.
    """
    search_url = f"{BASE_URL}esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'email': EMAIL,
        'format': 'json'
    }
    
    logger.info(f"Searching PubMed for: {query}")
    
    response = requests.get(search_url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if 'esearchresult' in data and 'idlist' in data['esearchresult']:
        pmids = data['esearchresult']['idlist']
        logger.info(f"Found {len(pmids)} articles for query '{query}'")
        return pmids
    else:
        logger.warning(f"No results found for query: {query}")
        return []

def fetch_abstracts(pmids):
    """
    Fetch abstracts for a list of PMIDs.
    
    Args:
        pmids (list): List of PMID strings.
        
    Returns:
        dict: Mapping of PMID -> abstract text.
    """
    fetch_url = f"{BASE_URL}efetch.fcgi"
    abstracts = {}
    
    logger.info(f"Fetching abstracts for {len(pmids)} PMIDs...")
    
    for pmid in pmids:
        params = {
            'id': pmid,
            'email': EMAIL,
            'format': 'abstract'
        }
        
        try:
            response = requests.get(fetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the abstract text from the response
            # The response is XML-like text
            soup = BeautifulSoup(response.text, 'html.parser')
            abstract_elem = soup.find('abstract')
            
            if abstract_elem:
                abstract_text = abstract_elem.get_text(separator=' ', strip=True)
                abstracts[pmid] = abstract_text
            else:
                # Fallback: use raw text if parsing fails
                abstracts[pmid] = response.text[:500]  # Truncate for logging
                
        except Exception as e:
            logger.warning(f"Failed to fetch abstract for PMID {pmid}: {e}")
            continue
        
        # Respect rate limits
        time.sleep(0.34)  # NCBI recommends < 3 requests/sec for unauthenticated
    
    logger.info(f"Successfully fetched {len(abstracts)} abstracts")
    return abstracts

def extract_effect_sizes(text):
    """
    Extract correlation coefficients (r) and p-values from text using regex.
    
    Args:
        text (str): Abstract text.
        
    Returns:
        dict: Extracted values or None if not found.
    """
    # Patterns for correlation coefficients
    # Matches: r = 0.5, r=0.5, r= 0.5, r = 0.5, r(123)=0.5, etc.
    r_pattern = r'r\s*=?\s*[-+]?\d*\.?\d+'
    p_pattern = r'p\s*[<>=]?\s*[-+]?\d*\.?\d+(?:e[-+]?\d+)?'
    
    r_matches = re.findall(r_pattern, text, re.IGNORECASE)
    p_matches = re.findall(p_pattern, text, re.IGNORECASE)
    
    if not r_matches:
        return None
    
    # Extract the first valid r value
    r_val = None
    for match in r_matches:
        try:
            # Extract just the number
            num_str = re.search(r'[-+]?\d*\.?\d+', match)
            if num_str:
                r_val = float(num_str.group())
                # Sanity check: r should be between -1 and 1
                if -1.0 <= r_val <= 1.0:
                    break
        except ValueError:
            continue
    
    if r_val is None:
        return None
    
    # Extract p-value (first one found)
    p_val = None
    for match in p_matches:
        try:
            num_str = re.search(r'[-+]?\d*\.?\d+(?:e[-+]?\d+)?', match)
            if num_str:
                p_val = float(num_str.group())
                if 0.0 <= p_val <= 1.0:
                    break
        except ValueError:
            continue
    
    return {
        'correlation_r': r_val,
        'p_value': p_val
    }

def extract_study_metadata(text, pmid):
    """
    Extract study metadata (n_samples, taxon_name, pathway) from text.
    
    This is a heuristic extraction based on common patterns in abstracts.
    
    Args:
        text (str): Abstract text.
        pmid (str): PMID for the study.
        
    Returns:
        dict: Metadata dictionary.
    """
    metadata = {
        'pmid': pmid,
        'study_id': f"PMC_{pmid}",
        'n_samples': None,
        'taxon_name': None,
        'pathway': None,
        'effect_direction': 'unknown'
    }
    
    # Try to find sample size
    n_pattern = r'n\s*=\s*(\d+)|sample\s*size\s*[=:]\s*(\d+)|participants?\s*[=:]\s*(\d+)'
    n_match = re.search(n_pattern, text, re.IGNORECASE)
    if n_match:
        for group in n_match.groups():
            if group:
                metadata['n_samples'] = int(group)
                break
    
    # Try to find taxon names (common bacteria)
    common_taxa = [
        'bifidobacterium', 'lactobacillus', 'faecalibacterium', 
        'clostridium', 'bacteroides', 'prevotella', 'ruminococcus',
        'escherichia', 'salmonella', 'streptococcus'
    ]
    text_lower = text.lower()
    for taxon in common_taxa:
        if taxon in text_lower:
            metadata['taxon_name'] = taxon.capitalize()
            break
    
    # Try to find pathways
    pathways = ['bdnf', 'hdac', 'scfa', 'serotonin', 'dopamine', 'inflammation']
    for pathway in pathways:
        if pathway in text_lower:
            metadata['pathway'] = pathway.upper()
            break
    
    # Determine effect direction
    r_val = metadata.get('correlation_r')
    if r_val is not None:
        metadata['effect_direction'] = 'positive' if r_val > 0 else 'negative'
    
    return metadata

def select_median_closeness(values, target=None):
    """
    If multiple values are extracted, select the one closest to the median.
    
    Args:
        values (list): List of values.
        target (float): Optional target (defaults to median).
        
    Returns:
        float: The value closest to the median.
    """
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    
    if target is None:
        target = np.median(values)
    
    return min(values, key=lambda x: abs(x - target))

def main():
    """Main entry point for literature extraction."""
    logger.info("Starting Literature Extraction Pipeline (T040a)...")
    
    # Define search queries
    queries = [
        '"gut microbiome" AND "cognitive flexibility"',
        '"microbiome" AND "BDNF"',
        '"SCFA" AND "HDAC"',
        '"gut-brain axis" AND "memory"'
    ]
    
    all_pmids = set()
    for query in queries:
        pmids = search_pubmed_ids(query, max_results=20)
        all_pmids.update(pmids)
    
    if not all_pmids:
        raise RuntimeError("No PubMed articles found for any query. Check internet connection and query terms.")
    
    logger.info(f"Total unique PMIDs found: {len(all_pmids)}")
    
    # Fetch abstracts
    abstracts = fetch_abstracts(list(all_pmids))
    
    if not abstracts:
        raise RuntimeError("Failed to fetch any abstracts from PubMed.")
    
    # Process each abstract
    results = []
    for pmid, abstract_text in abstracts.items():
        # Extract effect sizes
        effect_data = extract_effect_sizes(abstract_text)
        
        if effect_data is None:
            continue  # Skip studies without extractable effect sizes
        
        # Extract metadata
        metadata = extract_study_metadata(abstract_text, pmid)
        
        # Merge data
        study_record = {
            'study_id': f"PMC_{pmid}",
            'pmid': pmid,
            'abstract_text': abstract_text[:1000],  # Truncate for storage
            'correlation_r': effect_data['correlation_r'],
            'p_value': effect_data['p_value'],
            'n_samples': metadata['n_samples'],
            'taxon_name': metadata['taxon_name'],
            'pathway': metadata['pathway'],
            'effect_direction': metadata['effect_direction']
        }
        
        results.append(study_record)
    
    if not results:
        raise RuntimeError("No studies with extractable effect sizes found in the abstracts.")
    
    # Filter by confidence (simple heuristic: require p-value or valid r)
    # In a real pipeline, we might use NER confidence scores
    valid_results = [r for r in results if r['correlation_r'] is not None]
    
    logger.info(f"Extracted {len(valid_results)} studies with valid effect sizes.")
    
    # Write output
    output_dir = get_data_raw()
    output_path = output_dir / "literature_metadata.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_results, f, indent=2)
    
    logger.info(f"Literature metadata written to: {output_path}")
    logger.info(f"Median correlation r: {np.median([r['correlation_r'] for r in valid_results]):.4f}")
    
    return 0

if __name__ == "__main__":
    import numpy as np
    sys.exit(main())