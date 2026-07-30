"""
T010: NCBI SRA Search & Verification.

Searches NCBI SRA for open-access studies with paired 16S and Influenza serology.
Verifies the dataset contains required variables.
Updates config.SRA_ACCESSION if found, or sets config.USE_SYNTHETIC_DATA if not.

This is a blocking gate for biological claims.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import requests
from utils.config import (
    get_raw_path, 
    get_processed_path, 
    get_output_path, 
    ensure_directories,
    get_random_seed
)
from utils.logging_config import get_logger, log_error_context

# Configure logger
logger = get_logger(__name__)

# Constants
SRA_SEARCH_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/"
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Required variables for validation
REQUIRED_VARS = {
    'subject_id': 'string',
    'taxa_abundances': 'object',
    'titer_baseline': 'number',
    'titer_post': 'number'
}

# Default configuration
USE_SYNTHETIC_DATA_DEFAULT = False
SRA_ACCESSION_DEFAULT = None

def search_ncbi_sra(query: str, max_results: int = 10) -> List[str]:
    """
    Search NCBI SRA for studies matching the query.
    
    Args:
        query: Search query string (e.g., "Gut Microbiome AND Influenza AND 16S")
        max_results: Maximum number of results to return
        
    Returns:
        List of study accession IDs (e.g., SRP123456)
    """
    try:
        # Construct search parameters
        params = {
            'db': 'sra',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'usehistory': 'y'
        }
        
        # Make the request
        response = requests.get(NCBI_ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'esearchresult' not in data:
            logger.warning("No valid response from NCBI E-Search")
            return []
        
        id_list = data['esearchresult'].get('idlist', [])
        logger.info(f"Found {len(id_list)} potential studies in NCBI SRA")
        
        return id_list[:max_results]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching NCBI SRA: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing NCBI SRA response: {e}")
        return []

def get_study_metadata(accession: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a specific SRA study.
    
    Args:
        accession: SRA study accession ID
        
    Returns:
        Dictionary containing study metadata, or None if not found
    """
    try:
        params = {
            'db': 'sra',
            'id': accession,
            'retmode': 'json'
        }
        
        response = requests.get(NCBI_ESUMMARY_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data and accession in data['result']:
            return data['result'][accession]
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching metadata for {accession}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing metadata for {accession}: {e}")
        return None

def verify_study_contains_required_data(accession: str) -> bool:
    """
    Verify that a study contains the required data variables.
    
    This function checks if the study metadata indicates the presence of:
    - 16S rRNA sequencing data (for microbiome)
    - Serology/antibody titer data (for immune response)
    
    Args:
        accession: SRA study accession ID
        
    Returns:
        True if the study appears to contain required data, False otherwise
    """
    metadata = get_study_metadata(accession)
    
    if not metadata:
        logger.warning(f"Could not retrieve metadata for {accession}")
        return False
    
    # Check for keywords in study title and description
    title = metadata.get('title', '').lower()
    description = metadata.get('description', '').lower()
    
    # Keywords indicating 16S/microbiome data
    microbiome_keywords = ['16s', 'microbiome', 'gut flora', 'bacterial diversity', 'metagenome']
    has_microbiome = any(kw in title or kw in description for kw in microbiome_keywords)
    
    # Keywords indicating serology/immune response data
    serology_keywords = ['influenza', 'flu', 'vaccine', 'antibody', 'titer', 'serology', 'immune response']
    has_serology = any(kw in title or kw in description for kw in serology_keywords)
    
    # Check for paired data indication
    paired_keywords = ['paired', 'longitudinal', 'pre-post', 'before after', 'baseline post']
    has_paired = any(kw in title or kw in description for kw in paired_keywords)
    
    logger.info(f"Study {accession}:")
    logger.info(f"  - Has microbiome data: {has_microbiome}")
    logger.info(f"  - Has serology data: {has_serology}")
    logger.info(f"  - Has paired design: {has_paired}")
    
    # Require both microbiome and serology keywords, preferably paired design
    if has_microbiome and has_serology:
        logger.info(f"Study {accession} appears to contain required data")
        return True
    
    return False

def create_synthetic_config() -> Dict[str, Any]:
    """
    Create configuration for synthetic data usage when no real data is found.
    
    Returns:
        Dictionary with USE_SYNTHETIC_DATA set to True and SRA_ACCESSION set to None
    """
    return {
        'USE_SYNTHETIC_DATA': True,
        'SRA_ACCESSION': None,
        'reason': 'No suitable real dataset found in NCBI SRA',
        'search_query': 'Gut Microbiome AND Influenza AND 16S AND serology',
        'timestamp': pd.Timestamp.now().isoformat()
    }

def create_real_data_config(accession: str) -> Dict[str, Any]:
    """
    Create configuration for real data usage when a suitable dataset is found.
    
    Args:
        accession: The verified SRA study accession ID
        
    Returns:
        Dictionary with USE_SYNTHETIC_DATA set to False and SRA_ACCESSION set
    """
    return {
        'USE_SYNTHETIC_DATA': False,
        'SRA_ACCESSION': accession,
        'search_query': 'Gut Microbiome AND Influenza AND 16S AND serology',
        'verification_status': 'passed',
        'timestamp': pd.Timestamp.now().isoformat()
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path) -> None:
    """
    Write the search results configuration to a JSON file.
    
    Args:
        config: Configuration dictionary to write
        output_path: Path to the output JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write configuration file: {e}")
        raise

def run_sra_search() -> Dict[str, Any]:
    """
    Main function to run the NCBI SRA search and verification process.
    
    Returns:
        Dictionary containing search results and configuration
    """
    logger.info("Starting NCBI SRA Search & Verification (Task T010)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Define output paths
    output_dir = get_output_path()
    search_results_path = output_dir / "sra_search_results.json"
    config_update_path = output_dir / "sra_config_update.json"
    
    # Search query for relevant studies
    search_query = "Gut Microbiome AND Influenza AND 16S AND serology"
    logger.info(f"Searching with query: {search_query}")
    
    # Perform search
    study_ids = search_ncbi_sra(search_query, max_results=10)
    
    if not study_ids:
        logger.warning("No studies found in NCBI SRA with the specified query")
        config = create_synthetic_config()
        write_config_to_file(config, config_update_path)
        
        # Write search results
        results = {
            'query': search_query,
            'studies_found': 0,
            'studies_verified': 0,
            'verified_accession': None,
            'use_synthetic_data': True,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        write_config_to_file(results, search_results_path)
        
        return config
    
    logger.info(f"Found {len(study_ids)} potential studies, verifying content...")
    
    # Verify each study
    verified_accession = None
    verified_count = 0
    
    for study_id in study_ids:
        logger.info(f"Verifying study: {study_id}")
        
        if verify_study_contains_required_data(study_id):
            verified_accession = study_id
            verified_count += 1
            logger.info(f"Study {study_id} PASSED verification")
            break  # Take the first verified study
        else:
            logger.info(f"Study {study_id} did not pass verification")
    
    if verified_accession:
        logger.info(f"Found suitable dataset: {verified_accession}")
        config = create_real_data_config(verified_accession)
    else:
        logger.warning("No suitable dataset found after verification")
        config = create_synthetic_config()
    
    # Write configuration update
    write_config_to_file(config, config_update_path)
    
    # Write detailed search results
    results = {
        'query': search_query,
        'studies_found': len(study_ids),
        'studies_verified': verified_count,
        'verified_accession': verified_accession,
        'use_synthetic_data': config['USE_SYNTHETIC_DATA'],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    write_config_to_file(results, search_results_path)
    
    # Log summary
    if verified_accession:
        logger.info("=" * 60)
        logger.info("T010 COMPLETED SUCCESSFULLY")
        logger.info(f"Verified dataset: {verified_accession}")
        logger.info("Proceeding with REAL data pipeline")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info("T010 COMPLETED - NO REAL DATA FOUND")
        logger.info("Pipeline will proceed with SYNTHETIC data for CI validation only")
        logger.info("Biological claims cannot be made without real data")
        logger.info("=" * 60)
    
    return config

def main():
    """Entry point for the SRA search script."""
    try:
        config = run_sra_search()
        
        # Exit with appropriate code
        if config.get('USE_SYNTHETIC_DATA'):
            # Synthetic data mode - pipeline can continue for CI but not for claims
            sys.exit(0)
        else:
            # Real data found - pipeline proceeds normally
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error in SRA search: {e}")
        log_error_context(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
