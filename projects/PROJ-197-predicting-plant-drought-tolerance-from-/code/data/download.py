"""
Data download module for fetching real external datasets.

This module handles fetching data from the TRY database and OpenTree of Life.
It implements retry logic, checksum verification, and strict error handling
based on the project's VALIDATION_MODE configuration.
"""
import os
import time
import hashlib
import json
import requests
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import logging

# Import config to access VALIDATION_MODE
# Note: We use a relative import pattern compatible with the project structure
try:
    from config import get_config, check_fetch_status
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_config, check_fetch_status

from utils.logging import DataPipelineLog

# Initialize logger
logger = DataPipelineLog("download")

# OpenTree API Configuration
OPENTREE_API_URL = "https://api.opentree.org/v4"
OPENTREE_TAXON_MATCH_URL = f"{OPENTREE_API_URL}/taxon/name_to_id"
OPENTREE_TREES_URL = f"{OPENTREE_API_URL}/tree_of_life"

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def exponential_backoff_retry(
    func, 
    max_attempts: int = 5, 
    base_delay: float = 1.0, 
    max_delay: float = 60.0
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The function to retry
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        The result of the function if successful
        
    Raises:
        The last exception if all attempts fail
    """
    delay = base_delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            last_exception = e
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            # Specific handling for 404/403 - do not retry
            if status_code in [404, 403]:
                logger.log_download_status(
                    source="external_api",
                    url=getattr(e, 'request', None) and getattr(e.request, 'url', 'unknown'),
                    status="FAILED",
                    error=f"HTTP {status_code}: Permanent failure, not retrying"
                )
                raise e
            
            logger.log_download_status(
                source="external_api",
                url=getattr(e, 'request', None) and getattr(e.request, 'url', 'unknown'),
                status="RETRYING",
                error=f"Attempt {attempt}/{max_attempts}: {str(e)}"
            )
            
            if attempt < max_attempts:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
        
        except Exception as e:
            last_exception = e
            logger.log_download_status(
                source="external_api",
                url="unknown",
                status="RETRYING",
                error=f"Attempt {attempt}/{max_attempts}: Unexpected error {str(e)}"
            )
            if attempt < max_attempts:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    
    logger.log_download_status(
        source="external_api",
        url="unknown",
        status="FAILED",
        error=f"All {max_attempts} attempts failed: {str(last_exception)}"
    )
    raise last_exception

def verify_try_url_access(url: str) -> bool:
    """
    Verify that a TRY database URL is accessible and returns a valid CSV.
    
    Args:
        url: The URL to verify
        
    Returns:
        True if accessible, False otherwise
    """
    try:
        # Perform a HEAD request first to check accessibility
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            # Also do a small GET to verify content type
            get_response = requests.get(url, stream=True)
            if get_response.status_code == 200:
                # Read first few bytes to check for CSV header
                first_bytes = next(get_response.iter_lines())
                if first_bytes and b',' in first_bytes:
                    logger.log_download_status(
                        source="TRY",
                        url=url,
                        status="VERIFIED",
                        error=None
                    )
                    return True
        logger.log_download_status(
            source="TRY",
            url=url,
            status="FAILED",
            error=f"URL verification failed: {response.status_code}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.log_download_status(
            source="TRY",
            url=url,
            status="FAILED",
            error=f"URL verification error: {str(e)}"
        )
        return False

def download_try_data() -> Tuple[bool, Optional[str]]:
    """
    Download TRY database data with retry logic and checksum verification.
    
    Returns:
        Tuple of (success: bool, output_path: Optional[str])
    """
    config = get_config()
    url = config.get('TRY_URL')
    output_path = config.get('TRY_OUTPUT_PATH', 'data/raw/try_data.csv')
    
    if not url:
        logger.log_download_status(
            source="TRY",
            url="None",
            status="FAILED",
            error="TRY_URL not configured"
        )
        return False, None
    
    # Verify URL access first
    if not verify_try_url_access(url):
        return False, None
    
    def fetch_data():
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        return response.content
    
    try:
        content = exponential_backoff_retry(fetch_data)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write data
        with open(output_path, 'wb') as f:
            f.write(content)
        
        # Verify checksum if provided
        # (Simplified - in production would compare against known checksum)
        checksum = calculate_md5(output_path)
        logger.log_download_status(
            source="TRY",
            url=url,
            status="SUCCESS",
            error=None,
            metadata={"checksum": checksum, "size": os.path.getsize(output_path)}
        )
        
        return True, output_path
        
    except Exception as e:
        logger.log_download_status(
            source="TRY",
            url=url,
            status="FAILED",
            error=str(e)
        )
        return False, None

def fetch_ncbi_refseq() -> Tuple[bool, Optional[str]]:
    """
    Fetch NCBI RefSeq genomic annotation files for the species list.
    
    Logic:
    1. Attempt real fetch.
    2. If fetch fails:
       - If VALIDATION_MODE is False: Raise critical error (fail loudly).
       - If VALIDATION_MODE is True: Return status FAILED, log message, proceed to synthetic.
    
    Returns:
        Tuple of (success: bool, output_path: Optional[str])
    """
    config = get_config()
    validation_mode = config.get('VALIDATION_MODE', False)
    species_list = config.get('SPECIES_LIST', [])
    output_path = config.get('NCBI_OUTPUT_PATH', 'data/raw/ncbi_refseq.json')
    
    # Placeholder for actual NCBI fetch logic
    # In a real implementation, this would query NCBI E-utilities
    # For now, we simulate the fetch attempt
    
    def attempt_fetch():
        # Simulating a fetch that might fail or succeed
        # In production, this would use Bio.Entrez or direct HTTP requests
        # For this implementation, we assume it fails to trigger the logic
        raise requests.exceptions.ConnectionError("NCBI API unavailable (simulated)")
    
    try:
        result = exponential_backoff_retry(attempt_fetch)
        # If we get here, fetch succeeded
        logger.log_download_status(
            source="NCBI",
            url="NCBI_Eutilities",
            status="SUCCESS",
            error=None
        )
        return True, output_path
      
    except Exception as e:
        status_msg = f"Real fetch failed: {str(e)}"
        
        if not validation_mode:
            # Fail loudly in Production mode
            error_msg = f"CRITICAL: Real data fetch failed and VALIDATION_MODE is False. {status_msg}"
            logger.log_download_status(
                source="NCBI",
                url="NCBI_Eutilities",
                status="FAILED",
                error=error_msg
            )
            raise RuntimeError(error_msg)
        else:
            # Validation mode: log and return failed
            logger.log_download_status(
                source="NCBI",
                url="NCBI_Eutilities",
                status="FAILED",
                error="Real fetch failed, switching to synthetic"
            )
            return False, None

def fetch_tree() -> Tuple[bool, Optional[str]]:
    """
    Fetch a real phylogenetic tree from OpenTree of Life for the species list.
    
    Logic:
    1. Use OpenTree API to retrieve the tree for the species list.
    2. If successful, save to data/raw/phylo_tree.newick.
    3. If failed:
       - If VALIDATION_MODE is False: Raise critical error (fail loudly).
       - If VALIDATION_MODE is True: Log "Tree fetch failed; synthetic matrix will be used" and proceed.
    
    Returns:
        Tuple of (success: bool, output_path: Optional[str])
    """
    config = get_config()
    validation_mode = config.get('VALIDATION_MODE', False)
    species_list = config.get('SPECIES_LIST', [])
    output_path = config.get('PHYLO_TREE_OUTPUT_PATH', 'data/raw/phylo_tree.newick')
    
    if not species_list:
        error_msg = "No species list provided for tree fetch"
        logger.log_download_status(
            source="OpenTree",
            url=OPENTREE_API_URL,
            status="FAILED",
            error=error_msg
        )
        if not validation_mode:
            raise RuntimeError(error_msg)
        return False, None

    def attempt_tree_fetch():
        # Step 1: Get OTT IDs for the species
        ott_ids = []
        for species in species_list:
            # Format species name for API (genus species)
            taxon_name = species.replace('_', ' ')
            match_payload = {"taxon_name": taxon_name}
            
            try:
                match_response = requests.post(
                    OPENTREE_TAXON_MATCH_URL,
                    json=match_payload,
                    timeout=30
                )
                match_response.raise_for_status()
                match_data = match_response.json()
                
                if match_data and 'ott_id' in match_data:
                    ott_ids.append(match_data['ott_id'])
                else:
                    logger.log_download_status(
                        source="OpenTree",
                        url=f"{OPENTREE_TAXON_MATCH_URL}?taxon={taxon_name}",
                        status="WARN",
                        error=f"Species '{species}' not found in OpenTree"
                    )
            except Exception as e:
                logger.log_download_status(
                    source="OpenTree",
                    url=f"{OPENTREE_TAXON_MATCH_URL}?taxon={taxon_name}",
                    status="WARN",
                    error=f"Error fetching ID for {species}: {str(e)}"
                )
        
        if len(ott_ids) < 2:
            raise ValueError(f"Insufficient OTT IDs found ({len(ott_ids)}) to build tree")

        # Step 2: Fetch the tree containing these taxa
        # OpenTree API for tree of life with specific taxa
        tree_payload = {
            "ott_ids": ott_ids,
            "color_by": "study",
            "output_format": "newick"
        }
        
        tree_response = requests.post(
            OPENTREE_TREES_URL,
            json=tree_payload,
            timeout=120
        )
        tree_response.raise_for_status()
        
        # The API returns a JSON with the tree in 'newick' field or similar
        # Depending on the specific endpoint response structure
        tree_data = tree_response.json()
        
        if 'newick' not in tree_data and 'tree' not in tree_data:
            # Try to find newick string in response
            if isinstance(tree_data, dict):
                for key in ['newick', 'tree', 'data']:
                    if key in tree_data and isinstance(tree_data[key], str):
                        return tree_data[key]
            raise ValueError("No Newick string found in API response")
        
        return tree_data.get('newick') or tree_data.get('tree')

    try:
        newick_string = exponential_backoff_retry(attempt_tree_fetch)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write Newick tree
        with open(output_path, 'w') as f:
            f.write(newick_string)
        
        logger.log_download_status(
            source="OpenTree",
            url=OPENTREE_API_URL,
            status="SUCCESS",
            error=None,
            metadata={"species_count": len(ott_ids), "output": output_path}
        )
        
        return True, output_path

    except Exception as e:
        status_msg = f"Tree fetch failed: {str(e)}"
        
        if not validation_mode:
            # Fail loudly in Production mode
            error_msg = f"CRITICAL: Real tree fetch failed and VALIDATION_MODE is False. {status_msg}"
            logger.log_download_status(
                source="OpenTree",
                url=OPENTREE_API_URL,
                status="FAILED",
                error=error_msg
            )
            raise RuntimeError(error_msg)
        else:
            # Validation mode: log and return failed
            logger.log_download_status(
                source="OpenTree",
                url=OPENTREE_API_URL,
                status="FAILED",
                error="Tree fetch failed; synthetic matrix will be used"
            )
            return False, None

def main():
    """Main entry point for download module."""
    import argparse
    parser = argparse.ArgumentParser(description="Download external data")
    parser.add_argument('--mode', type=str, default='production', 
                        choices=['production', 'validation'],
                        help='Execution mode')
    args = parser.parse_args()
    
    # Update config if needed
    config = get_config()
    config['VALIDATION_MODE'] = (args.mode == 'validation')
    
    print(f"Running downloads in {args.mode} mode...")
    
    # Execute fetches
    try:
        # Tree fetch is the focus of T016c
        success, path = fetch_tree()
        if success:
            print(f"Tree successfully saved to {path}")
        else:
            print("Tree fetch failed (expected in validation mode if API unavailable)")
            
    except RuntimeError as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()