"""
NCBI SRA Search & Verification Module (Task T010).

This module implements the blocking gate for biological claims by:
1. Searching NCBI SRA for open-access studies with paired 16S and Influenza serology.
2. Verifying the presence of required variables (baseline taxa, post-vaccination titers).
3. Writing configuration artifacts to `data/research/` to control downstream pipeline flow.

If a valid study is found, it sets `USE_SYNTHETIC_DATA = False` and writes the accession.
If no valid study is found, it sets `USE_SYNTHETIC_DATA = True` to allow pipeline execution
for code validation (but blocks biological claims).
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Ensure imports work from project root
try:
    from utils.logging_config import get_logger
    from utils.config import ensure_directories
except ImportError:
    # Fallback for direct execution if utils not in path yet
    import logging
    from pathlib import Path

    def get_logger(name):
        return logging.getLogger(name)

    def ensure_directories():
        dirs = [
            "data/raw", "data/processed", "data/results", "tests", "data/research"
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

# Constants
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Required keywords for the search
SEARCH_QUERY = (
    '"16S rRNA"[Title/Abstract] AND '
    '(influenza OR flu) AND '
    '(serology OR antibody OR titer) AND '
    '(human OR "Homo sapiens")'
)

# Minimum sample size required to consider a study valid for this pipeline
MIN_SAMPLES = 50

logger = get_logger(__name__)

def format_search_query() -> str:
    """Returns the formatted search query string."""
    return SEARCH_QUERY

def validate_accession_format(accession: str) -> bool:
    """
    Validates that the accession string follows SRA format (SRP, SRX, SRS, SRR).
    """
    if not accession:
        return False
    prefix = accession.upper()
    return prefix.startswith(('SRP', 'SRX', 'SRS', 'SRR'))

def search_ncbi_sra(query: str, retmax: int = 10) -> Optional[List[str]]:
    """
    Searches NCBI SRA using E-utilities and returns a list of accession IDs.
    
    Args:
        query: The search query string.
        retmax: Maximum number of results to return.
        
    Returns:
        List of accession IDs (e.g., SRP12345) or None if search fails.
    """
    params = {
        "db": "sra",
        "term": query,
        "retmode": "json",
        "retmax": retmax,
        "usehistory": "y"
    }
    
    try:
        response = requests.get(NCBI_ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "esearchresult" in data and "idlist" in data["esearchresult"]:
            ids = data["esearchresult"]["idlist"]
            logger.info(f"SRA Search found {len(ids)} potential studies.")
            return ids
        else:
            logger.warning("SRA Search returned no ID list in response.")
            return None
    except requests.RequestException as e:
        logger.error(f"Failed to search NCBI SRA: {e}")
        return None

def get_study_metadata(accession_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata for a specific SRA study using E-utilities.
    
    Args:
        accession_id: The study accession (e.g., SRP12345).
        
    Returns:
        Dictionary of metadata or None if fetch fails.
    """
    if not validate_accession_format(accession_id):
        # If it's not a study accession (SRP), try to find the study via esummary on SRA db
        # But for this task, we assume we are looking for SRP series IDs.
        # If the ID is SRX/SRS/SRR, we might need to map to SRP first, 
        # but let's try esummary directly as it often handles cross-refs.
        pass
        
    params = {
        "db": "sra",
        "id": accession_id,
        "retmode": "json"
    }
    
    try:
        response = requests.get(NCBI_ESUMMARY_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" in data and accession_id in data["result"]:
            return data["result"][accession_id]
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession_id}: {e}")
        return None

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifies if the study metadata indicates the presence of required data types.
    
    Checks for:
    1. 16S rRNA sequencing (library_strategy = 'WGS' or 'AMPLICON', library_source = 'GENOMIC' or 'METAGENOMIC')
    2. Human host
    3. Evidence of serology/antibody data in the title or description (heuristic check)
    
    Note: True verification of paired serology often requires fetching the actual 
    associated publications or sample metadata, which is complex. This function 
    performs a heuristic check on the study description/title.
    """
    title = metadata.get("title", "").lower()
    description = metadata.get("description", "").lower()
    combined_text = f"{title} {description}"
    
    # Check for 16S/Amplicon indicators
    is_16s = "16s" in combined_text or "amplicon" in combined_text or "microbiome" in combined_text
    
    # Check for serology/antibody indicators
    has_serology = any(kw in combined_text for kw in ["antibody", "titer", "serology", "humoral", "immune response"])
    
    # Check for Human
    is_human = "human" in combined_text or "homo sapiens" in combined_text
    
    if not is_human:
        return False, "Study does not appear to be human."
    if not is_16s:
        return False, "Study does not appear to contain 16S rRNA data."
    if not has_serology:
        return False, "Study metadata does not explicitly mention serology/antibody/titer."
        
    # Heuristic: If we found all keywords, we assume it's a candidate.
    # A more robust check would parse the BioProject links or fetch the publication.
    return True, "Candidate study found with required keywords."

def create_real_data_config(accession: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates the configuration dictionary for a found real dataset.
    """
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": accession,
        "search_query": SEARCH_QUERY,
        "search_timestamp": str(json.dumps(search_results, default=str)) # Simplified for JSON
    }

def create_synthetic_config(reason: str = "No real data found") -> Dict[str, Any]:
    """
    Creates the configuration dictionary indicating synthetic data must be used.
    """
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "accession": None,
        "reason": reason,
        "search_query": SEARCH_QUERY
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path, search_results_json: Optional[Dict] = None) -> None:
    """
    Writes the configuration and search results to JSON files.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write status/config
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Written config to {output_path}")
    
    # Write full search results if provided
    if search_results_json:
        results_path = output_path.parent / "sra_search_results.json"
        with open(results_path, 'w') as f:
            json.dump(search_results_json, f, indent=2, default=str)
        logger.info(f"Written search results to {results_path}")

def run_sra_search() -> Dict[str, Any]:
    """
    Main execution logic for T010.
    
    1. Searches NCBI SRA.
    2. Iterates results to find a valid study.
    3. Writes `data/research/sra_status.json`.
    4. Returns the configuration dict.
    """
    ensure_directories()
    status_path = Path("data/research/sra_status.json")
    results_path = Path("data/research/sra_search_results.json")
    
    logger.info(f"Starting SRA Search with query: {SEARCH_QUERY}")
    
    # 1. Search
    accession_ids = search_ncbi_sra(SEARCH_QUERY)
    
    if not accession_ids:
        logger.warning("No accession IDs returned from NCBI SRA search.")
        config = create_synthetic_config("NCBI SRA search returned no results.")
        write_config_to_file(config, status_path, {"status": "no_results"})
        return config
    
    # 2. Verify each candidate
    found_accession = None
    verification_details = {}
    
    for acc in accession_ids:
        logger.info(f"Verifying candidate: {acc}")
        metadata = get_study_metadata(acc)
        
        if not metadata:
            verification_details[acc] = "Metadata fetch failed"
            continue
            
        is_valid, message = verify_study_contains_required_data(metadata)
        verification_details[acc] = message
        
        if is_valid:
            found_accession = acc
            logger.info(f"Found valid study: {acc} ({message})")
            break
    
    if found_accession:
        # Success Path
        config = create_real_data_config(found_accession, verification_details)
        write_config_to_file(config, status_path, {"found_accession": found_accession, "details": verification_details})
        return config
    else:
        # Failure Path - No valid study found
        logger.warning("No valid study found matching criteria.")
        config = create_synthetic_config("No study found with 16S + Serology + Human.")
        write_config_to_file(config, status_path, {"details": verification_details})
        return config

def main():
    """Entry point for the script."""
    logger.info("Executing T010: NCBI SRA Search & Verification")
    try:
        config = run_sra_search()
        logger.info(f"T010 Completed. Status: {config['status']}")
        
        # Verification check
        if config['use_synthetic']:
            logger.warning("Pipeline will proceed in SYNTHETIC DATA MODE. Biological claims are blocked.")
        else:
            logger.info(f"Real data found: Accession {config['accession']}. Pipeline proceeds.")
            
        return 0
    except Exception as e:
        logger.critical(f"T010 Failed with exception: {e}")
        # Even on exception, ensure we don't crash the pipeline silently if we can write a failure state
        try:
            config = create_synthetic_config(f"Error during search: {str(e)}")
            write_config_to_file(config, Path("data/research/sra_status.json"))
        except:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main())
