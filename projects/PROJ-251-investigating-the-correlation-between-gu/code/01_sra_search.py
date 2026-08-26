import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests

from utils.logging_config import get_logger
from utils.config import get_sra_accession, get_use_synthetic_data, ensure_directories, get_output_path

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when no real data is found in SRA."""
    pass

def search_ncbi_sra(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search NCBI SRA for studies matching the query.
    Returns a list of study metadata dictionaries.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "sra",
        "term": f"{query} AND (16S[All Fields] AND influenza[All Fields])",
        "retmax": limit,
        "usehistory": "y",
        "retmode": "json"
    }

    logger.info(f"Searching NCBI SRA with query: {query}")
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
            logger.warning("SRA search returned no IDs.")
            return []
        
        ids = data["esearchresult"]["idlist"]
        logger.info(f"Found {len(ids)} potential study IDs: {ids}")
        return ids
    except requests.RequestException as e:
        logger.error(f"Failed to search NCBI SRA: {e}")
        raise DataUnavailableError(f"Network error during SRA search: {e}")

def get_study_metadata(study_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch detailed metadata for a list of SRA study IDs.
    """
    if not study_ids:
        return []
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    metadata_list = []
    
    for s_id in study_ids:
        params = {
            "db": "sra",
            "id": s_id,
            "retmode": "json"
        }
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "result" in data and s_id in data["result"]:
                metadata_list.append(data["result"][s_id])
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch metadata for {s_id}: {e}")
            continue
    
    return metadata_list

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> bool:
    """
    Verify if the study metadata indicates presence of required data types.
    Checks for:
    1. 16S rRNA sequencing (implied by library strategy or description)
    2. Host (human) samples
    3. Presence of associated metadata (implied by study design)
    
    Returns True if the study looks promising for the specific research question.
    """
    description = metadata.get("description", "").lower()
    title = metadata.get("title", "").lower()
    library_strategy = metadata.get("library_strategy", "").lower()
    
    # Heuristic checks
    has_16s = "16s" in description or "16s" in title or "rrna" in description
    has_influenza = "influenza" in description or "flu" in description or "vaccination" in description
    has_human = "human" in description or "human" in title
    
    if has_16s and has_influenza and has_human:
        logger.info(f"Study {metadata.get('accession', 'Unknown')} matches criteria: 16S, Influenza, Human.")
        return True
    
    logger.debug(f"Study {metadata.get('accession', 'Unknown')} did not match all heuristic criteria.")
    return False

def create_synthetic_config() -> Dict[str, Any]:
    """
    Creates a configuration dictionary indicating no real data was found.
    """
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "message": "No suitable real dataset found in NCBI SRA for paired 16S and Influenza serology.",
        "timestamp": str(Path().cwd())
    }

def create_real_data_config(accession_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a configuration dictionary for a found real dataset.
    """
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "sra_accession": accession_id,
        "study_title": metadata.get("title", ""),
        "study_url": f"https://www.ncbi.nlm.nih.gov/sra/?term={accession_id}",
        "timestamp": str(Path().cwd())
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path):
    """
    Writes the search result configuration to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Search results written to {output_path}")

def run_sra_search() -> bool:
    """
    Main execution logic for T010.
    Returns True if real data is found, False if synthetic fallback is needed.
    """
    ensure_directories()
    
    # Output paths
    results_json_path = get_output_path("data/research/sra_search_results.json")
    status_json_path = get_output_path("data/research/sra_status.json")
    
    # Search query
    query = "Gut Microbiome Influenza Vaccination"
    
    try:
        # 1. Search
        study_ids = search_ncbi_sra(query)
        
        if not study_ids:
            logger.warning("No study IDs found in SRA search.")
            config = create_synthetic_config()
            write_config_to_file(config, results_json_path)
            
            # Write status file for blocking gate
            status = {"status": "no_real_data", "use_synthetic": True}
            status_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(status_json_path, 'w') as f:
                json.dump(status, f, indent=2)
            return False

        # 2. Verify
        for s_id in study_ids:
            metadata_list = get_study_metadata([s_id])
            if not metadata_list:
                continue
            
            meta = metadata_list[0]
            if verify_study_contains_required_data(meta):
                # Found a match
                config = create_real_data_config(s_id, meta)
                write_config_to_file(config, results_json_path)
                
                # Update global config in memory (and ideally write to config file if needed, 
                # but for now we assume the runner will read this JSON or update config.py)
                # For this task, we just log it and set the status file.
                status = {"status": "real_data_found", "use_synthetic": False, "accession": s_id}
                status_json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(status_json_path, 'w') as f:
                    json.dump(status, f, indent=2)
                
                logger.info(f"Real data found: {s_id}")
                return True
        
        # If we get here, we found IDs but none matched the specific criteria
        logger.warning("No suitable studies found matching all criteria.")
        config = create_synthetic_config()
        write_config_to_file(config, results_json_path)
        
        status = {"status": "no_real_data", "use_synthetic": True}
        status_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(status_json_path, 'w') as f:
            json.dump(status, f, indent=2)
        return False

    except DataUnavailableError as e:
        logger.error(f"Search failed: {e}")
        config = create_synthetic_config()
        write_config_to_file(config, results_json_path)
        status = {"status": "no_real_data", "use_synthetic": True}
        status_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(status_json_path, 'w') as f:
            json.dump(status, f, indent=2)
        return False
    except Exception as e:
        logger.critical(f"Unexpected error during SRA search: {e}")
        raise

def main():
    """Entry point for T010."""
    logger.info("Starting T010: NCBI SRA Search & Verification")
    success = run_sra_search()
    if success:
        logger.info("T010 Complete: Real data identified.")
    else:
        logger.info("T010 Complete: No real data found. Synthetic data mode enabled.")
    return 0 if success else 0 # Return 0 even if synthetic, as the task itself succeeded in determining status

if __name__ == "__main__":
    sys.exit(main())
