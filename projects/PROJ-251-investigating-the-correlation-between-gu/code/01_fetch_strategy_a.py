import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_sra_accession, get_research_path, get_raw_path, get_use_synthetic_data
from utils.sra_fetcher import DataUnavailableError, fetch_otu_table, fetch_serology_metadata
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def write_sra_status(status: str, use_synthetic: bool, accession: Optional[str] = None, reason: Optional[str] = None):
    """
    Write the sra_status.json file to indicate the outcome of the data fetch.
    """
    research_path = get_research_path()
    research_path.mkdir(parents=True, exist_ok=True)
    status_file = research_path / "sra_status.json"
    
    status_data = {
        "status": status,
        "use_synthetic": use_synthetic
    }
    if accession:
        status_data["accession"] = accession
    if reason:
        status_data["reason"] = reason
        
    import json
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Wrote sra_status.json: {status_data}")

def fetch_strategy_a_data():
    """
    Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
    
    Method:
    1. Retrieve SRA_ACCESSION from config.
    2. Attempt to fetch pre-processed OTU table and serology metadata.
       - Tries to download from a known public repository structure (e.g., Figshare/Zenodo linked to SRA).
       - Falls back to direct SRA metadata extraction if raw data is available but pre-processed is not.
    3. If fetch fails (404, timeout, or DataUnavailableError):
       - Write sra_status.json with status "fetch_failed" and use_synthetic=True.
       - Raise DataUnavailableError.
    
    Output:
    - data/raw/otutable.csv
    - data/raw/serology.csv
    """
    accession = get_sra_accession()
    raw_path = get_raw_path()
    raw_path.mkdir(parents=True, exist_ok=True)
    
    if not accession:
        logger.error("No SRA_ACCESSION found in config. Cannot proceed with Strategy A.")
        write_sra_status("no_accession", True, reason="SRA_ACCESSION not set")
        raise DataUnavailableError("SRA_ACCESSION not configured.")

    logger.info(f"Attempting to fetch data for accession: {accession}")
    
    try:
        # Attempt to fetch OTU table
        # Note: In a real scenario, this would query a specific repository API 
        # or download from a URL constructed from the accession.
        # For this implementation, we assume the utils.sra_fetcher handles the logic
        # of locating the pre-processed files (CSV/BIOM) associated with the accession.
        otu_table_path = raw_path / "otutable.csv"
        serology_path = raw_path / "serology.csv"
        
        # Fetch OTU Table
        logger.info("Fetching OTU table...")
        fetch_otu_table(accession, str(otu_table_path))
        
        # Fetch Serology Metadata
        logger.info("Fetching serology metadata...")
        fetch_serology_metadata(accession, str(serology_path))
        
        # Verify files exist and are non-empty
        if not otu_table_path.exists() or otu_table_path.stat().st_size == 0:
            raise DataUnavailableError("OTU table fetch resulted in empty or missing file.")
        if not serology_path.exists() or serology_path.stat().st_size == 0:
            raise DataUnavailableError("Serology metadata fetch resulted in empty or missing file.")
            
        logger.info(f"Successfully fetched data: {otu_table_path}, {serology_path}")
        write_sra_status("real_data_found", False, accession=accession)
        
        return True

    except (DataUnavailableError, FileNotFoundError, requests.exceptions.RequestException) as e:
        logger.error(f"Strategy A fetch failed: {str(e)}")
        # Write failure status
        write_sra_status("fetch_failed", True, accession=accession, reason=str(e))
        # Re-raise to halt pipeline as per requirements
        raise DataUnavailableError(f"Strategy A failed: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during Strategy A fetch: {str(e)}")
        write_sra_status("fetch_failed", True, accession=accession, reason=f"Unexpected error: {str(e)}")
        raise DataUnavailableError(f"Unexpected error: {str(e)}") from e

def main():
    """
    Entry point for Strategy A data fetching.
    """
    logger.info("Starting Strategy A: Fetch pre-processed OTU table and serology metadata")
    try:
        success = fetch_strategy_a_data()
        if success:
            logger.info("Strategy A completed successfully.")
            return 0
        else:
            logger.error("Strategy A returned failure status.")
            return 1
    except DataUnavailableError as e:
        logger.error(f"Data unavailable error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Critical error in Strategy A: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
