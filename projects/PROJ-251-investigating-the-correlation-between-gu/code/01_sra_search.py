import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from existing API surface
from utils.config import get_sra_accession, get_use_synthetic_data, get_research_path, ensure_directories
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
SRA_SEARCH_QUERY = '16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)'
MAX_RESULTS = 10
MIN_REQUIRED_FIELDS = ['titer_baseline', 'titer_post']

def format_search_query(query: str) -> str:
    """Format the search query for NCBI E-utilities."""
    return query.replace(" ", "%20")

def validate_accession_format(accession: str) -> bool:
    """Validate that an accession ID matches expected SRA format (SRP, SRX, SRR, etc.)."""
    if not accession:
        return False
    valid_prefixes = ('SRP', 'SRX', 'SRR', 'ERP', 'DRP', 'DRX')
    return any(accession.startswith(prefix) for prefix in valid_prefixes)

def search_ncbi_sra(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search NCBI SRA database using E-utilities.
    Returns a dictionary with search results or error info.
    """
    params = {
        'db': 'sra',
        'term': query,
        'retmode': 'json',
        'retmax': max_results
    }
    
    try:
        response = requests.get(NCBI_ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'esearchresult' in data:
            result = data['esearchresult']
            count = int(result.get('count', 0))
            ids = result.get('idlist', [])
            
            logger.info(f"SRA Search found {count} potential studies.")
            
            if count == 0:
                return {
                    'success': True,
                    'count': 0,
                    'ids': [],
                    'message': 'No studies found matching query.'
                }
            
            return {
                'success': True,
                'count': count,
                'ids': ids,
                'message': f'Found {count} studies.'
            }
        else:
            logger.error(f"Unexpected response format: {data}")
            return {
                'success': False,
                'message': 'Invalid response format from NCBI.'
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during SRA search: {e}")
        return {
            'success': False,
            'message': f'Network error: {str(e)}'
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {
            'success': False,
            'message': f'Invalid JSON response: {str(e)}'
        }

def get_study_metadata(accession_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed metadata for a specific SRA study.
    Returns None if fetch fails.
    """
    params = {
        'db': 'sra',
        'id': accession_id,
        'retmode': 'json',
        'rettype': 'metadata'
    }
    
    try:
        response = requests.get(NCBI_EFETCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Could not fetch metadata for {accession_id}: {e}")
        return None

def verify_study_contains_required_data(metadata: Dict[str, Any]) -> bool:
    """
    Verify if the study metadata indicates presence of required data types.
    This is a heuristic check based on available metadata fields.
    """
    if not metadata:
        return False
    
    # Check for 16S rRNA indication
    has_16s = False
    has_serology = False
    
    # Check study title and description
    title = metadata.get('title', '').lower()
    description = metadata.get('description', '').lower()
    combined_text = f"{title} {description}"
    
    if '16s' in combined_text or '16 s' in combined_text or 'rrna' in combined_text:
        has_16s = True
        
    if any(term in combined_text for term in ['serolog', 'antibod', 'titer', 'haemagglutination', 'hai']):
        has_serology = True
    
    # Check for experimental design keywords in study attributes
    study_attributes = metadata.get('attributes', [])
    for attr in study_attributes:
        key = attr.get('key', '').lower()
        value = attr.get('value', '').lower()
        text = f"{key} {value}"
        
        if '16s' in text or 'rrna' in text:
            has_16s = True
        if 'serolog' in text or 'antibod' in text or 'titer' in text:
            has_serology = True
    
    return has_16s and has_serology

def create_real_data_config(accession_id: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
    """Create configuration for real data path."""
    return {
        'status': 'real_data_found',
        'use_synthetic': False,
        'accession': accession_id,
        'search_count': search_results.get('count', 0),
        'search_query': SRA_SEARCH_QUERY,
        'timestamp': None  # Will be set by caller
    }

def create_synthetic_config(reason: str = "No real data found") -> Dict[str, Any]:
    """Create configuration for synthetic data path."""
    return {
        'status': 'no_real_data',
        'use_synthetic': True,
        'accession': None,
        'reason': reason,
        'search_query': SRA_SEARCH_QUERY,
        'timestamp': None  # Will be set by caller
    }

def write_config_to_file(config: Dict[str, Any], output_path: Path):
    """Write configuration to JSON file."""
    import datetime
    config['timestamp'] = datetime.datetime.now().isoformat()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to {output_path}")

def run_sra_search() -> bool:
    """
    Main function to perform SRA search and verification.
    Returns True if successful, False otherwise.
    """
    logger.info("Starting NCBI SRA Search and Verification (Task T010)...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Perform search
    search_results = search_ncbi_sra(SRA_SEARCH_QUERY, MAX_RESULTS)
    
    if not search_results.get('success'):
        logger.error(f"Search failed: {search_results.get('message')}")
        # Write synthetic config since search failed
        sra_status_config = create_synthetic_config(f"Search failed: {search_results.get('message')}")
        write_config_to_file(sra_status_config, Path("data/research/sra_status.json"))
        
        # Write search results
        write_config_to_file(search_results, Path("data/research/sra_search_results.json"))
        return False
    
    # Write search results
    write_config_to_file(search_results, Path("data/research/sra_search_results.json"))
    
    if search_results.get('count', 0) == 0:
        logger.warning("No studies found matching the search query.")
        sra_status_config = create_synthetic_config("No studies found matching search query.")
        write_config_to_file(sra_status_config, Path("data/research/sra_status.json"))
        return False
    
    # Try to verify the first few studies for required data
    accession_id = None
    for study_id in search_results.get('ids', [])[:5]:  # Check up to 5 studies
        logger.info(f"Verifying study: {study_id}")
        metadata = get_study_metadata(study_id)
        
        if metadata and verify_study_contains_required_data(metadata):
            accession_id = study_id
            logger.info(f"Verified study {study_id} contains required data types.")
            break
    
    if accession_id:
        # Real data found
        sra_status_config = create_real_data_config(accession_id, search_results)
        write_config_to_file(sra_status_config, Path("data/research/sra_status.json"))
        
        # Update config module if needed (for downstream tasks)
        # Note: In a real pipeline, this would update the config file or env
        logger.info(f"Real data found: Accession {accession_id}")
        return True
    else:
        # No suitable study found
        logger.warning("No suitable study found with required data types.")
        sra_status_config = create_synthetic_config("No suitable study found with required data types.")
        write_config_to_file(sra_status_config, Path("data/research/sra_status.json"))
        return False

def main():
    """Entry point for script execution."""
    logger.info("Executing T010: NCBI SRA Search & Verification")
    success = run_sra_search()
    
    if success:
        logger.info("T010 completed successfully: Real data found.")
        sys.exit(0)
    else:
        logger.warning("T010 completed: No real data found, synthetic path enabled.")
        sys.exit(0)  # Exit 0 as this is expected behavior for the gate

if __name__ == "__main__":
    main()
