import os
import sys
import logging
import socket
import urllib.request
from typing import Tuple, Optional
from .logging import get_logger
from .config import get_project_root

# ZINC15 is hosted on HuggingFace Datasets.
# The canonical source for ZINC15 in the `datasets` library is 'moleculenet/zinc'.
# We verify connectivity by attempting to list this specific dataset metadata.
ZINC15_DATASET_ID = "moleculenet/zinc"
ZINC15_TIMEOUT = 15

def check_huggingface_connection(timeout: int = ZINC15_TIMEOUT) -> Tuple[bool, Optional[str]]:
    """
    Check connectivity to HuggingFace datasets, specifically verifying access to ZINC15.
    
    This function attempts to load the metadata for the ZINC15 dataset.
    If the connection fails or the dataset is unreachable, it returns False.
    
    Args:
        timeout: Connection timeout in seconds.
        
    Returns:
        Tuple of (success, error_message).
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        # Attempt to fetch info for the specific ZINC15 dataset to ensure it exists and is reachable
        api.dataset_info(ZINC15_DATASET_ID)
        return True, None
    except Exception as e:
        return False, str(e)

def check_open_data_pubchem_connection(timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Check connectivity to OpenDataPubChem (NCBI PubChem PUG REST).
    
    Args:
        timeout: Connection timeout in seconds.
        
    Returns:
        Tuple of (success, error_message).
    """
    try:
        # Try to connect to a known PubChem endpoint
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/cids/JSON"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'llmXive/1.0')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True, None
            return False, f"HTTP {response.status}"
    except Exception as e:
        return False, str(e)

def run_network_checks() -> Tuple[bool, bool, str]:
    """
    Run all network connectivity checks required for data ingestion.
    
    Returns:
        Tuple of (hf_ok, pubchem_ok, combined_message).
    """
    logger = get_logger("network_check")
    logger.info("Running network connectivity checks for ZINC15 and OpenDataPubChem...")
    
    hf_ok, hf_error = check_huggingface_connection()
    pubchem_ok, pubchem_error = check_open_data_pubchem_connection()
    
    message = ""
    if not hf_ok:
        message += f"HuggingFace (ZINC15) check failed: {hf_error}\n"
    if not pubchem_ok:
        message += f"OpenDataPubChem check failed: {pubchem_error}\n"
    
    if hf_ok and pubchem_ok:
        message = "All network checks passed."
        logger.info(message)
    else:
        logger.warning(message)
    
    return hf_ok, pubchem_ok, message

def main() -> None:
    """
    Main entry point for network checks.
    Runs before any ingestion tasks to verify access to data sources.
    If the connection to ZINC15 fails or the URL is unreachable, 
    this function raises a ConnectionError immediately and halts the pipeline.
    """
    hf_ok, pubchem_ok, message = run_network_checks()
    print(message)
    
    # T049 Requirement: Fail loudly if ZINC15 is unreachable.
    if not hf_ok:
        raise ConnectionError(f"Critical Failure: Unable to connect to ZINC15 source. Pipeline halted. Error: {message}")
    
    # Optional: Warn if PubChem is down, but ZINC15 is the primary dependency for this task
    if not pubchem_ok:
        logging.warning(f"PubChem check failed, but ZINC15 is available. Warning: {message}")
        
    if hf_ok and pubchem_ok:
        sys.exit(0)
    else:
        # This point is reached if PubChem failed but ZINC15 passed (handled above)
        # or if ZINC15 failed (handled by raise).
        # If we are here, ZINC15 passed.
        sys.exit(0)

if __name__ == "__main__":
    main()