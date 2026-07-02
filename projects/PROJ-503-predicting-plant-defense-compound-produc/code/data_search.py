"""
Module for searching public omics repositories (GEO, Metabolomics Workbench)
for relevant plant defense studies.
"""
import json
import logging
from typing import List, Dict, Any
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_geo(
    query: str,
    retmax: int = 100,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Search NCBI GEO (Gene Expression Omnibus) via the E-utilities API.
    
    Args:
        query: Search query string (e.g., "Arabidopsis herbivore stress")
        retmax: Maximum number of results to return
        timeout: Request timeout in seconds
        
    Returns:
        List of dictionaries containing search results (ID, title, summary, etc.)
        
    Raises:
        requests.RequestException: If the API request fails
        ValueError: If no results are found
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    params = {
        "db": "gds",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "usehistory": "y"
    }
    
    logger.info(f"Searching GEO with query: {query}")
    
    try:
        response = requests.get(base_url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        if "result" not in data or "ids" not in data["result"]:
            logger.warning("No results found in GEO response structure")
            return []
        
        ids = data["result"]["ids"]
        logger.info(f"Found {len(ids)} GEO series IDs")
        
        # Fetch detailed metadata for each ID
        details = []
        if ids:
            # Batch fetch details
            id_list = ",".join(ids)
            detail_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            detail_params = {
                "db": "gds",
                "id": id_list,
                "retmode": "json"
            }
            
            detail_response = requests.get(detail_url, params=detail_params, timeout=timeout)
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            
            for item_id in ids:
                if item_id in detail_data["result"]:
                    item = detail_data["result"][item_id]
                    details.append({
                        "accession": item_id,
                        "title": item.get("title", "Unknown"),
                        "summary": item.get("summary", "No summary available"),
                        "organism": item.get("organism", "Unknown"),
                        "series_type": item.get("series_type", "Unknown"),
                        "sample_count": item.get("sample_count", 0)
                    })
        
        return details
        
    except requests.exceptions.Timeout:
        logger.error(f"Request to GEO timed out after {timeout} seconds")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to GEO failed: {e}")
        raise


def search_geo_organism_stress(
    organism: str,
    stress_keywords: List[str],
    retmax: int = 100
) -> List[Dict[str, Any]]:
    """
    Construct and execute a GEO search for a specific organism under stress conditions.
    
    Args:
        organism: Organism name (e.g., "Arabidopsis thaliana")
        stress_keywords: List of stress-related keywords to include
        retmax: Maximum number of results
        
    Returns:
        List of search result dictionaries
    """
    # Construct query: organism AND (stress1 OR stress2 OR ...)
    stress_clause = " OR ".join(stress_keywords)
    query = f'"{organism}" AND ({stress_clause}) AND "plant"'
    
    return search_geo(query, retmax=retmax)
