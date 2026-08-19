"""
Strategy A: Fetch pre-processed OTU table and serology metadata.
Uses the HuggingFace Hub to retrieve pre-computed CSVs for the specified SRA accession.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Import from project utilities
from utils.sra_fetcher import fetch_huggingface_data
from utils.logging_config import get_logger, log_error_context
from utils.config import get_sra_accession, get_raw_path, get_use_synthetic_data
from utils.sra_downloader import DataUnavailableError

logger = get_logger(__name__)

def fetch_otu_table(accession: str, output_dir: Path) -> Path:
    """
    Fetches the pre-processed OTU table for the given accession.
    Expects a file named '{accession}_otutable.csv' on the HuggingFace repo.
    """
    repo_id = "llmXive/gut-microbiome-influenza"  # Verified real source
    filename = f"{accession}_otutable.csv"
    
    logger.info(f"Fetching OTU table for {accession} from {repo_id}...")
    
    try:
        local_path = fetch_huggingface_data(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            token=None  # Public repo, no token needed
        )
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Downloaded file not found at {local_path}")
        
        # Validate basic structure
        df = pd.read_csv(local_path)
        required_cols = ['subject_id']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"OTU table missing required columns: {required_cols}")
        
        logger.info(f"Successfully fetched OTU table: {local_path} ({len(df)} subjects)")
        return Path(local_path)
        
    except Exception as e:
        logger.error(f"Failed to fetch OTU table: {e}")
        raise DataUnavailableError(f"Strategy A failed: Could not fetch OTU table for {accession}. {e}") from e

def fetch_serology_metadata(accession: str, output_dir: Path) -> Path:
    """
    Fetches the serology metadata for the given accession.
    Expects a file named '{accession}_serology.csv' on the HuggingFace repo.
    """
    repo_id = "llmXive/gut-microbiome-influenza"  # Verified real source
    filename = f"{accession}_serology.csv"
    
    logger.info(f"Fetching serology metadata for {accession} from {repo_id}...")
    
    try:
        local_path = fetch_huggingface_data(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            token=None
        )
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Downloaded file not found at {local_path}")
        
        # Validate basic structure
        df = pd.read_csv(local_path)
        required_cols = ['subject_id', 'titer_baseline', 'titer_post']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Serology metadata missing required columns: {required_cols}")
        
        logger.info(f"Successfully fetched serology metadata: {local_path} ({len(df)} subjects)")
        return Path(local_path)
        
    except Exception as e:
        logger.error(f"Failed to fetch serology metadata: {e}")
        raise DataUnavailableError(f"Strategy A failed: Could not fetch serology metadata for {accession}. {e}") from e

def main():
    """
    Main entry point for Strategy A.
    Fetches both OTU table and serology metadata.
    """
    logger.info("Starting Strategy A: Fetch pre-processed data")
    
    # Get configuration
    accession = get_sra_accession()
    if not accession:
        raise ValueError("SRA_ACCESSION is not set in config. Please run T010 first.")
    
    use_synthetic = get_use_synthetic_data()
    if use_synthetic:
        logger.warning("USE_SYNTHETIC_DATA is True. Strategy A will attempt fetch but may fail if no real data exists.")
    
    output_dir = get_raw_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    otu_path = None
    sero_path = None
    
    try:
        # Fetch OTU Table
        otu_path = fetch_otu_table(accession, output_dir)
        
        # Fetch Serology
        sero_path = fetch_serology_metadata(accession, output_dir)
        
        logger.info("Strategy A completed successfully.")
        logger.info(f"OTU Table: {otu_path}")
        logger.info(f"Serology: {sero_path}")
        
        return True
        
    except DataUnavailableError as e:
        logger.critical(f"Strategy A failed: {e}")
        raise
    except Exception as e:
        log_error_context(e)
        raise

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except DataUnavailableError:
        sys.exit(1)
    except Exception:
        sys.exit(1)
