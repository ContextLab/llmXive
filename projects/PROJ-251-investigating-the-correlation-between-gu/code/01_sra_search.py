import os
import sys
import logging
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project utilities from the provided API surface
from utils.logging_config import get_logger
from utils.config import (
    get_env_var,
    get_sra_accession,
    get_use_synthetic_data,
    ensure_directories,
    get_research_path,
    get_raw_path,
    get_processed_path,
    get_results_path,
)

logger = get_logger(__name__)

# Constants for the specific search query required by the task
SRA_SEARCH_QUERY = (
    '"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) '
    'AND (human OR Homo sapiens)"'
)

# NCBI E-utilities base URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

class DataUnavailableError(Exception):
    """Raised when no suitable real data is found in SRA."""
    pass

def format_search_query() -> str:
    """Returns the formatted search query string."""
    return SRA_SEARCH_QUERY

def validate_accession_format(accession: str) -> bool:
    """Validates that an accession string matches expected SRA patterns."""
    if not accession:
        return False
    # SRA accessions usually start with SRX, SRS, SRP, etc.
    valid_prefixes = ("SRX", "SRS", "SRP", "SRR")
    return any(accession.startswith(prefix) for prefix in valid_prefixes)

def search_ncbi_sra(query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches NCBI SRA using E-utilities.
    Returns a dictionary containing search results (count, IDs, etc.).
    """
    params = {
        "db": "sra",
        "term": query,
        "retmode": "json",
        "retmax": 10,  # Fetch top 10 results to inspect
    }
    if api_key:
        params["api_key"] = api_key

    logger.info(f"Searching NCBI SRA with query: {query}")
    try:
        response = requests.get(ESearch_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to search NCBI SRA: {e}")
        raise DataUnavailableError(f"Network error during SRA search: {e}")

def get_study_metadata(accession_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches detailed metadata for a specific SRA accession.
    """
    params = {
        "db": "sra",
        "id": accession_id,
        "retmode": "json",
    }
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(EFETCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession_id}: {e}")
        return {}

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> bool:
    """
    Verifies if the study metadata suggests the presence of required data:
    - 16S rRNA sequencing
    - Influenza/Flu context
    - Serology/Antibody/Titer measurements
    - Human subjects
    """
    # Basic heuristic checks on metadata fields
    # In a real production system, this would parse complex XML/JSON structures
    # from the SRA record to find specific library strategies and titles.
    
    title = metadata.get("title", "").lower()
    description = metadata.get("description", "").lower()
    experiment = metadata.get("experiment", {}).get("attributes", [])
    
    # Combine text for search
    text_content = f"{title} {description}".lower()
    
    # Check for required keywords
    has_16s = "16s" in text_content or "16s rna" in text_content
    has_flu = "influenza" in text_content or "flu" in text_content
    has_serology = "serology" in text_content or "antibody" in text_content or "titer" in text_content
    has_human = "human" in text_content or "homo sapiens" in text_content

    # Heuristic: Must have 16s, Flu, and (Serology or Human context)
    # Since the search query already filters for these, we verify the specific record
    # actually looks like it contains the data types.
    if has_16s and has_flu and has_serology:
        return True
    
    # If it has 16s and Flu, and explicitly mentions Human, it might be a candidate
    # but we strictly need serology/titer mention for the "immune response" aspect
    if has_16s and has_flu and has_human and has_serology:
        return True

    logger.debug(f"Study {metadata.get('accession', 'unknown')} failed verification. "
                 f"16s:{has_16s}, Flu:{has_flu}, Serology:{has_serology}, Human:{has_human}")
    return False

def create_real_data_config(accession_id: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
    """Creates the configuration dictionary for a found real dataset."""
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": accession_id,
        "search_query": SRA_SEARCH_QUERY,
        "search_result_count": search_results.get("esearchresult", {}).get("count", 0),
        "url": f"https://www.ncbi.nlm.nih.gov/sra/?term={accession_id}"
    }

def create_synthetic_config() -> Dict[str, Any]:
    """Creates the configuration dictionary when no real data is found."""
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "accession": None,
        "search_query": SRA_SEARCH_QUERY,
        "message": "No suitable real data found in NCBI SRA matching criteria."
    }

def write_config_to_file(config: Dict[str, Any], filepath: Path) -> None:
    """Writes the configuration dictionary to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {filepath}")

def run_sra_search() -> Dict[str, Any]:
    """
    Main logic for T010: Search NCBI SRA and verify data existence.
    Returns the final status configuration.
    """
    ensure_directories()
    research_path = get_research_path()
    
    # Paths for output artifacts
    search_results_path = research_path / "sra_search_results.json"
    status_path = research_path / "sra_status.json"

    # Get API key if available
    api_key = get_env_var("NCBI_API_KEY")

    try:
        # Perform the search
        results = search_ncbi_sra(SRA_SEARCH_QUERY, api_key)
        
        esearch_result = results.get("esearchresult", {})
        count = int(esearch_result.get("count", 0))
        id_list = esearch_result.get("idlist", [])

        logger.info(f"SRA Search returned {count} results.")

        if count == 0:
            logger.warning("No results found in NCBI SRA.")
            config = create_synthetic_config()
            write_config_to_file(config, search_results_path)
            write_config_to_file(config, status_path)
            return config

        # Iterate through top results to find a valid one
        valid_accession = None
        for accession in id_list:
            logger.info(f"Verifying accession: {accession}")
            metadata = get_study_metadata(accession, api_key)
            
            if verify_study_contains_required_data(metadata):
                valid_accession = accession
                logger.info(f"Found valid study: {accession}")
                break

        if valid_accession:
            config = create_real_data_config(valid_accession, results)
            write_config_to_file(config, search_results_path)
            write_config_to_file(config, status_path)
            return config
        else:
            logger.warning("No suitable study found among search results.")
            config = create_synthetic_config()
            write_config_to_file(config, search_results_path)
            write_config_to_file(config, status_path)
            return config

    except DataUnavailableError as e:
        logger.error(f"Data search failed: {e}")
        config = create_synthetic_config()
        write_config_to_file(config, search_results_path)
        write_config_to_file(config, status_path)
        return config
    except Exception as e:
        logger.error(f"Unexpected error during SRA search: {e}")
        raise

def main():
    """Entry point for the SRA Search task."""
    logger.info("Starting T010: NCBI SRA Search & Verification")
    config = run_sra_search()
    
    # Verification step
    if config.get("use_synthetic"):
        logger.warning("Synthetic data mode enabled. Pipeline will proceed with synthetic data.")
    else:
        logger.info(f"Real data found. Accession: {config.get('accession')}")
    
    logger.info("T010 completed.")
    return config

if __name__ == "__main__":
    main()
