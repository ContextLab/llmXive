import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from utils.config import get_sra_accession, ensure_directories, get_raw_path, get_output_path
from utils.logging_config import get_logger, log_error_context

# Custom exception for data availability issues
class DataUnavailableError(Exception):
    """Raised when the requested data is not found or unavailable."""
    pass

def search_ncbi_sra(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search NCBI SRA for studies matching the query.
    
    Args:
        query: Search query string (e.g., "gut microbiome influenza vaccination")
        max_results: Maximum number of results to return
        
    Returns:
        List of study metadata dictionaries
    """
    logger = get_logger(__name__)
    base_url = "https://www.ebi.ac.uk/ena/browser/api/xml"
    
    # Using ENA as it often has better API support for SRA searches
    search_url = "https://www.ebi.ac.uk/ena/browser/api/search"
    params = {
        "query": query,
        "format": "json",
        "limit": max_results
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        return results.get("results", [])
    except requests.RequestException as e:
        logger.error(f"Failed to search NCBI SRA: {e}")
        raise DataUnavailableError(f"Failed to search NCBI SRA: {e}")

def get_study_metadata(accession: str) -> Dict[str, Any]:
    """
    Get detailed metadata for a specific SRA study.
    
    Args:
        accession: SRA study accession (e.g., SRP123456)
        
    Returns:
        Dictionary containing study metadata
    """
    logger = get_logger(__name__)
    url = f"https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse XML response (ENA returns XML)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        metadata = {
            "accession": accession,
            "title": None,
            "description": None,
            "samples": [],
            "runs": []
        }
        
        # Extract title
        title_elem = root.find(".//title")
        if title_elem is not None:
            metadata["title"] = title_elem.text
        
        # Extract description
        desc_elem = root.find(".//description")
        if desc_elem is not None:
            metadata["description"] = desc_elem.text
        
        # Extract samples and runs
        for study in root.findall(".//STUDY"):
            accession_elem = study.find("ACCESSION")
            if accession_elem is not None:
                metadata["accession"] = accession_elem.text
            
            # Look for sample links
            sample_links = study.findall(".//SAMPLE_LINK/SAMPLE_LINK_ACCESSION")
            for link in sample_links:
                if link.text:
                    metadata["samples"].append(link.text)
            
            # Look for run links
            run_links = study.findall(".//RUN_LINK/RUN_LINK_ACCESSION")
            for link in run_links:
                if link.text:
                    metadata["runs"].append(link.text)
        
        return metadata
    except Exception as e:
        logger.error(f"Failed to get metadata for {accession}: {e}")
        raise DataUnavailableError(f"Failed to get metadata for {accession}: {e}")

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> bool:
    """
    Verify that the study metadata indicates it contains required data types.
    
    Args:
        metadata: Study metadata dictionary
        
    Returns:
        True if the study appears to contain required data, False otherwise
    """
    logger = get_logger(__name__)
    
    # Check if title or description mentions key terms
    title = metadata.get("title", "").lower()
    description = metadata.get("description", "").lower()
    text = f"{title} {description}"
    
    required_terms = ["gut", "microbiome", "influenza", "vaccination", "serology"]
    found_terms = [term for term in required_terms if term in text]
    
    if len(found_terms) < 3:
        logger.warning(f"Study {metadata.get('accession')} missing key terms. Found: {found_terms}")
        return False
    
    # Check for presence of samples and runs
    if not metadata.get("samples") or not metadata.get("runs"):
        logger.warning(f"Study {metadata.get('accession')} has no samples or runs")
        return False
    
    logger.info(f"Study {metadata.get('accession')} appears to contain required data types")
    return True

def create_synthetic_config() -> Dict[str, Any]:
    """
    Create configuration for synthetic data mode.
    
    Returns:
        Configuration dictionary for synthetic data
    """
    return {
        "USE_SYNTHETIC_DATA": True,
        "SRA_ACCESSION": None,
        "reason": "No real data found after exhaustive search"
    }

def create_real_data_config(accession: str) -> Dict[str, Any]:
    """
    Create configuration for real data mode.
    
    Args:
        accession: Verified SRA accession
        
    Returns:
        Configuration dictionary for real data
    """
    return {
        "USE_SYNTHETIC_DATA": False,
        "SRA_ACCESSION": accession,
        "reason": f"Verified real data found: {accession}"
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path) -> None:
    """
    Write configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        output_path: Path to output file
    """
    logger = get_logger(__name__)
    try:
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write config to {output_path}: {e}")
        raise

def run_sra_search() -> Dict[str, Any]:
    """
    Main function to search NCBI SRA and verify data availability.
    
    Returns:
        Dictionary containing search results and configuration
    """
    logger = get_logger(__name__)
    logger.info("Starting NCBI SRA search and verification")
    
    # Ensure directories exist
    ensure_directories()
    
    # Define search query
    query = "gut microbiome influenza vaccination serology"
    
    # Search for studies
    try:
        studies = search_ncbi_sra(query, max_results=20)
    except DataUnavailableError as e:
        logger.error(f"Search failed: {e}")
        config = create_synthetic_config()
        write_config_to_file(config, get_output_path("sra_search_config.json"))
        return config
    
    if not studies:
        logger.warning("No studies found matching query")
        config = create_synthetic_config()
        write_config_to_file(config, get_output_path("sra_search_config.json"))
        return config
    
    # Verify each study
    verified_accession = None
    for study in studies:
        accession = study.get("study_accession") or study.get("accession")
        if not accession:
            continue
        
        logger.info(f"Verifying study: {accession}")
        try:
            metadata = get_study_metadata(accession)
            if verify_study_contains_required_data(metadata):
                verified_accession = accession
                logger.info(f"Verified study: {accession}")
                break
        except DataUnavailableError as e:
            logger.warning(f"Study {accession} verification failed: {e}")
            continue
    
    # Create configuration based on findings
    if verified_accession:
        config = create_real_data_config(verified_accession)
        logger.info(f"Real data found: {verified_accession}")
    else:
        config = create_synthetic_config()
        logger.warning("No suitable real data found, falling back to synthetic")
    
    # Write configuration
    write_config_to_file(config, get_output_path("sra_search_config.json"))
    
    return config

def main():
    """Entry point for SRA search script."""
    logger = get_logger(__name__)
    try:
        result = run_sra_search()
        logger.info(f"SRA search completed. Result: {result}")
        return 0
    except Exception as e:
        log_error_context(logger, e, "SRA search failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())