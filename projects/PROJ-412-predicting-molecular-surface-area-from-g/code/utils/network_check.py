import os
import sys
import logging
import socket
import urllib.request
from typing import Tuple, Optional
from .logging import get_logger
from .config import get_project_root

def check_huggingface_connection(timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Check connectivity to HuggingFace datasets (specifically for ZINC15 access).
    
    Args:
        timeout: Connection timeout in seconds.
        
    Returns:
        Tuple of (success, error_message).
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        # Try to list a small public dataset to verify connectivity
        # Using a generic search to avoid specific dataset dependency issues
        # We search for "zinc" to ensure the ZINC15 source is reachable
        api.list_datasets(search="zinc", limit=1)
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
    Exits with code 1 if any check fails.
    """
    hf_ok, pubchem_ok, message = run_network_checks()
    print(message)
    if not (hf_ok and pubchem_ok):
        sys.exit(1)

if __name__ == "__main__":
    main()