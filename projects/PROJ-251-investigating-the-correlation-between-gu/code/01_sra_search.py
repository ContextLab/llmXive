import os
import sys
import logging
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

from utils.logging_config import get_logger
from utils.config import get_sra_accession, get_use_synthetic_data, ensure_directories, get_ncbi_api_key

logger = get_logger(__name__)

# E-utilities base URL
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def format_search_query() -> str:
    """
    Constructs the specific search query required by T010.
    """
    return '"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)"'

def validate_accession_format(accession: str) -> bool:
    """
    Validates that the accession string looks like a valid SRA study/run accession.
    SRA studies usually start with SRP, SRX, SRS, etc.
    """
    if not accession or not isinstance(accession, str):
        return False
    # Basic check for common SRA prefixes
    prefixes = ('SRP', 'SRX', 'SRS', 'ERR', 'DRR', 'ERR')
    return accession.startswith(prefixes)

def search_ncbi_sra(query: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Searches NCBI SRA using E-utilities. Returns the first Study Accession ID found.
    Returns None if no results found or error occurs.
    """
    search_url = f"{EUTILS_BASE}/esearch.fcgi"
    params = {
        "db": "sra",
        "term": query,
        "retmode": "json",
        "retmax": 1,
        "usehistory": "y"
    }
    if api_key:
        params["api_key"] = api_key

    logger.info(f"Searching NCBI SRA with query: {query}")
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "esearchresult" in data and "idlist" in data["esearchresult"]:
            id_list = data["esearchresult"]["idlist"]
            if id_list:
                accession = id_list[0]
                logger.info(f"Found SRA ID: {accession}")
                return accession
            else:
                logger.warning("No IDs found in search results.")
        else:
            logger.warning("Unexpected response structure or empty result.")
        
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during SRA search: {e}")
        return None

def get_study_metadata(accession: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata for a specific SRA accession to verify it contains required data.
    """
    summary_url = f"{EUTILS_BASE}/esummary.fcgi"
    params = {
        "db": "sra",
        "id": accession,
        "retmode": "json"
    }
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(summary_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and accession in data["result"]:
            return data["result"][accession]
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching metadata for {accession}: {e}")
        return None

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> bool:
    """
    Verifies that the study metadata indicates presence of 16S and Serology/Immune data.
    This is a heuristic check based on title, description, or study type.
    """
    if not metadata:
        return False
    
    # Heuristics: Check title and description for keywords
    title = str(metadata.get('title', '')).lower()
    desc = str(metadata.get('description', '')).lower()
    study_type = str(metadata.get('study_type', '')).lower()
    
    # Look for 16S/RNA-seq indicators
    has_microbiome = any(kw in title or kw in desc for kw in ['16s', 'microbiome', 'metagenomics', 'rRNA'])
    
    # Look for immune/serology indicators
    has_immune = any(kw in title or kw in desc for kw in ['influenza', 'flu', 'vaccine', 'antibody', 'titer', 'serology', 'immune response'])
    
    # If we have both, it's a candidate
    if has_microbiome and has_immune:
        logger.info(f"Study {metadata.get('accession', 'unknown')} appears to contain required data types.")
        return True
    
    logger.warning(f"Study {metadata.get('accession', 'unknown')} metadata does not clearly indicate required data types.")
    return False

class DataUnavailableError(Exception):
    """Raised when real data cannot be found or accessed."""
    pass

def create_real_data_config(accession: str, output_dir: Path) -> Dict[str, Any]:
    """
    Creates the configuration object for real data found.
    """
    url = f"https://www.ncbi.nlm.nih.gov/sra/?term={accession}"
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": accession,
        "url": url,
        "search_query": format_search_query()
    }

def create_synthetic_config(output_dir: Path) -> Dict[str, Any]:
    """
    Creates the configuration object when no real data is found.
    """
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "accession": None,
        "url": None,
        "search_query": format_search_query()
    }

def write_config_to_file(config: Dict[str, Any], filepath: Path):
    """
    Writes the configuration dictionary to a JSON file.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {filepath}")

def run_sra_search() -> Dict[str, Any]:
    """
    Main logic for T010: Search NCBI SRA and verify data existence.
    Returns the status config dictionary.
    """
    ensure_directories()
    output_dir = Path("data/research")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    search_results_path = output_dir / "sra_search_results.json"
    status_path = output_dir / "sra_status.json"
    
    query = format_search_query()
    api_key = get_ncbi_api_key()
    
    # 1. Search
    accession = search_ncbi_sra(query, api_key)
    
    if not accession:
        logger.warning("No SRA studies found matching the query.")
        config = create_synthetic_config(output_dir)
        write_config_to_file(config, status_path)
        write_config_to_file({"status": "no_results", "query": query}, search_results_path)
        return config
    
    # 2. Verify Metadata
    metadata = get_study_metadata(accession, api_key)
    if not metadata:
        logger.warning(f"Could not retrieve metadata for accession {accession}.")
        # If we can't verify, we treat as not found to be safe
        config = create_synthetic_config(output_dir)
        write_config_to_file(config, status_path)
        write_config_to_file({"status": "metadata_fetch_failed", "accession": accession}, search_results_path)
        return config
    
    if not verify_study_contains_required_data(metadata):
        logger.warning(f"Accession {accession} does not appear to contain required data types.")
        config = create_synthetic_config(output_dir)
        write_config_to_file(config, status_path)
        write_config_to_file({"status": "data_type_mismatch", "accession": accession, "metadata": metadata}, search_results_path)
        return config
    
    # 3. Success
    logger.info(f"Real data found and verified: {accession}")
    config = create_real_data_config(accession, output_dir)
    write_config_to_file(config, status_path)
    write_config_to_file({"status": "success", "accession": accession, "metadata_summary": {k: v for k, v in metadata.items() if k in ['title', 'description', 'study_type']}}, search_results_path)
    
    # Update global config if needed (though config.py usually reads from files or env)
    # For this pipeline, we assume the downstream tasks read sra_status.json
    return config

def main():
    """
    Entry point for the SRA Search task.
    """
    try:
        config = run_sra_search()
        if config["use_synthetic"]:
            logger.info("No real data found. Pipeline must use synthetic data.")
            sys.exit(0) # Success in finding out we need synthetic
        else:
            logger.info(f"Real data found. Accession: {config['accession']}")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in SRA Search: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
