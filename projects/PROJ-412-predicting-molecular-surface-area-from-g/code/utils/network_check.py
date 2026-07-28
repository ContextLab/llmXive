"""
Pre-flight network connectivity check for data sources.

This module verifies access to ZINC15 (via Hugging Face datasets)
and OpenDataPubChem before any ingestion tasks begin.
"""

import os
import sys
import logging
from typing import Tuple, Optional

from .logging import get_logger
from .config import get_project_root

# Configure logger for this module
logger = get_logger(__name__)


def check_huggingface_connection(dataset_name: str, streaming: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if we can connect to Hugging Face to access a specific dataset.

    Args:
        dataset_name: The dataset identifier (e.g., 'Zinc15')
        streaming: Whether to use streaming mode

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        # Attempt to import the datasets library
        from datasets import load_dataset
        
        logger.info(f"Checking connection to Hugging Face for dataset: {dataset_name}")
        
        # Try to load the dataset in streaming mode (minimal download)
        # This will fail immediately if there's no connection or if the dataset doesn't exist
        ds = load_dataset(dataset_name, split="train", streaming=streaming)
        
        # Attempt to fetch the first item to verify the stream is valid
        # We don't iterate further to keep the check fast
        first_item = next(iter(ds))
        
        if first_item is not None:
            logger.info(f"Successfully connected to Hugging Face and verified dataset: {dataset_name}")
            return True, None
        else:
            error_msg = f"Dataset {dataset_name} returned empty stream"
            logger.error(error_msg)
            return False, error_msg
            
    except ImportError as e:
        error_msg = f"Failed to import 'datasets' library: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to connect to Hugging Face for {dataset_name}: {e}"
        logger.error(error_msg)
        return False, error_msg


def check_open_data_pubchem_connection() -> Tuple[bool, Optional[str]]:
    """
    Check if we can connect to OpenDataPubChem (via Hugging Face datasets).
    
    OpenDataPubChem is typically hosted on Hugging Face as a dataset.
    We verify connectivity by attempting to load a small portion.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        from datasets import load_dataset
        
        logger.info("Checking connection to OpenDataPubChem via Hugging Face")
        
        # OpenDataPubChem is often available as 'open_data_pubchem' or similar on HF
        # We try the most common identifier
        dataset_id = "open_data_pubchem"
        
        # Try to load in streaming mode
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Verify the stream works
        first_item = next(iter(ds))
        
        if first_item is not None:
            logger.info("Successfully connected to OpenDataPubChem via Hugging Face")
            return True, None
        else:
            error_msg = "OpenDataPubChem dataset returned empty stream"
            logger.error(error_msg)
            return False, error_msg
            
    except ImportError as e:
        error_msg = f"Failed to import 'datasets' library: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        # If the specific dataset ID is not found, try alternative names or report the error
        error_msg = f"Failed to connect to OpenDataPubChem: {e}"
        logger.error(error_msg)
        return False, error_msg


def run_network_checks() -> bool:
    """
    Run all pre-flight network connectivity checks.

    This function checks access to both ZINC15 and OpenDataPubChem.
    At least one source must be available for the pipeline to proceed.

    Returns:
        True if at least one source is accessible, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("Starting pre-flight network connectivity checks")
    logger.info("=" * 60)

    zinc15_success, zinc15_error = check_huggingface_connection("Zinc15")
    pubchem_success, pubchem_error = check_open_data_pubchem_connection()

    logger.info("-" * 60)
    logger.info("Connectivity Check Results:")
    logger.info(f"  ZINC15: {'PASS' if zinc15_success else 'FAIL'}")
    if not zinc15_success:
        logger.info(f"    Error: {zinc15_error}")
    
    logger.info(f"  OpenDataPubChem: {'PASS' if pubchem_success else 'FAIL'}")
    if not pubchem_success:
        logger.info(f"    Error: {pubchem_error}")
    logger.info("-" * 60)

    if zinc15_success or pubchem_success:
        logger.info("At least one data source is accessible. Pipeline can proceed.")
        return True
    else:
        logger.critical("CRITICAL: No data sources are accessible. Cannot proceed with ingestion.")
        logger.critical("Please check your network connection and firewall settings.")
        return False


def main():
    """Main entry point for the network check script."""
    # Setup logging if not already configured
    if not logger.handlers:
        setup_logging = globals().get('setup_logging')
        if setup_logging:
            setup_logging()
        else:
            # Fallback to basic config
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )

    success = run_network_checks()
    
    if not success:
        logger.error("Network checks failed. Exiting.")
        sys.exit(1)
    else:
        logger.info("Network checks passed. Ready for ingestion.")
        sys.exit(0)


if __name__ == "__main__":
    main()