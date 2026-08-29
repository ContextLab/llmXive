import os
import sys
import logging
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_sra_accession, get_use_synthetic_data, ensure_directories
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

# NCBI E-utilities base URL
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def format_search_query() -> str:
    """Construct the specific search query for SRA studies."""
    return (
        '"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)"'
    )

def validate_accession_format(accession: str) -> bool:
    """Validate that the accession string looks like a real SRA accession."""
    if not accession:
        return False
    # SRA accessions typically start with SRP, SRS, SRX, or SRR
    prefixes = ('SRP', 'SRS', 'SRX', 'SRR')
    return any(accession.upper().startswith(p) for p in prefixes)

def search_ncbi_sra(query: str, max_results: int = 10) -> Optional[str]:
    """
    Search NCBI SRA using E-utilities.
    Returns the first valid accession ID found, or None if no results.
    """
    params = {
        'db': 'sra',
        'term': query,
        'retmode': 'json',
        'retmax': max_results
    }

    try:
        logger.info(f"Searching NCBI SRA with query: {query}")
        response = requests.get(ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'esearchresult' not in data:
            logger.error("Invalid response structure from NCBI E-utilities")
            return None

        id_list = data['esearchresult'].get('idlist', [])
        if not id_list:
            logger.warning("No results found in SRA search")
            return None

        # Return the first accession ID
        accession = id_list[0]
        logger.info(f"Found SRA accession: {accession}")
        return accession

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during SRA search: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None

def get_study_metadata(accession: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a specific SRA study to verify content.
    """
    params = {
        'db': 'sra',
        'id': accession,
        'retmode': 'json'
    }

    try:
        response = requests.get(EFETCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # NCBI E-utilities for SRA often returns a list of studies
        studies = data.get('SRAStudies', [])
        if not studies:
            logger.warning(f"No metadata found for accession {accession}")
            return None

        study = studies[0]
        return study

    except Exception as e:
        logger.error(f"Failed to fetch metadata for {accession}: {e}")
        return None

def verify_study_contains_required_data(accession: str) -> bool:
    """
    Verify that the study likely contains 16S and serology data.
    This is a heuristic check based on title/description.
    """
    metadata = get_study_metadata(accession)
    if not metadata:
        return False

    # Heuristic: Check if the title or description mentions relevant keywords
    # Note: Real verification would require downloading and inspecting samples
    title = metadata.get('Title', '').lower()
    description = metadata.get('Description', '').lower()
    combined = f"{title} {description}"

    required_keywords = ['16s', 'influenza', 'flu']
    found_keywords = [kw for kw in required_keywords if kw in combined]

    if len(found_keywords) >= 2:
        logger.info(f"Study {accession} appears to contain required data types.")
        return True

    logger.warning(f"Study {accession} metadata does not strongly indicate required data types.")
    return False

class DataUnavailableError(Exception):
    """Raised when real data cannot be found or accessed."""
    pass

def create_real_data_config(accession: str, url: str) -> Dict[str, Any]:
    """Create configuration object for real data found."""
    return {
        "status": "real_data_found",
        "accession": accession,
        "url": url,
        "use_synthetic": False,
        "timestamp": str(datetime.now())
    }

def create_synthetic_config() -> Dict[str, Any]:
    """Create configuration object indicating synthetic data fallback."""
    return {
        "status": "no_real_data",
        "accession": None,
        "url": None,
        "use_synthetic": True,
        "reason": "No suitable SRA study found with paired 16S and serology data",
        "timestamp": str(datetime.now())
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path) -> None:
    """Write the configuration dictionary to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {output_path}")

def run_sra_search() -> Dict[str, Any]:
    """
    Main entry point for SRA search and verification.
    Returns the configuration dictionary.
    """
    ensure_directories()
    search_query = format_search_query()
    output_dir = Path("data/research")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_file = output_dir / "sra_search_results.json"
    status_file = output_dir / "sra_status.json"

    # Perform search
    accession = search_ncbi_sra(search_query)

    if not accession:
        logger.warning("No SRA accession found. Marking for synthetic data fallback.")
        config = create_synthetic_config()
        write_config_to_file(config, results_file)
        write_config_to_file(config, status_file)
        return config

    # Verify the study
    if not verify_study_contains_required_data(accession):
        logger.warning(f"Found accession {accession} but could not verify data content. Falling back to synthetic.")
        config = create_synthetic_config()
        write_config_to_file(config, results_file)
        write_config_to_file(config, status_file)
        return config

    # Construct URL
    sra_url = f"https://www.ncbi.nlm.nih.gov/sra/?term={accession}"

    # Success
    logger.info(f"Verified real data source: {accession}")
    config = create_real_data_config(accession, sra_url)
    
    # Update global config variable in memory (simulated for this script)
    # In a real pipeline, this would update a shared state or env var
    
    write_config_to_file(config, results_file)
    write_config_to_file(config, status_file)
    
    return config

def main():
    """Script entry point."""
    try:
        result = run_sra_search()
        if result.get("use_synthetic"):
            print(f"Status: {result['status']}. Synthetic data will be used.")
            sys.exit(0) # Exit 0 as this is a valid outcome for the pipeline
        else:
            print(f"Status: Real data found. Accession: {result['accession']}")
            sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error in SRA search: {e}")
        with log_error_context("sra_search_error"):
            raise
        sys.exit(1)

if __name__ == "__main__":
    main()
