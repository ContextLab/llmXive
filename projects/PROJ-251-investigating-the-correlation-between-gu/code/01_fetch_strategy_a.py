import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional
import requests
import json

from utils.config import get_sra_accession, get_use_synthetic_data, get_raw_path, ensure_directories
from utils.logging_config import get_logger, log_error_context
from utils.sra_fetcher import DataUnavailableError, fetch_otu_table, fetch_serology_metadata

logger = get_logger(__name__)

def main():
    """
    T011a: Implement Strategy A: Fetch pre-processed OTU table and serology metadata.
    This script attempts to fetch real data based on the SRA accession in config.
    If fetching fails, it raises DataUnavailableError (fails loudly).
    """
    logger.info("Starting Strategy A: Fetching real data from SRA repository.")
    
    ensure_directories()
    raw_path = get_raw_path()
    sra_accession = get_sra_accession()
    use_synthetic = get_use_synthetic_data()

    if use_synthetic:
        logger.warning("Configuration indicates synthetic data should be used (USE_SYNTHETIC_DATA=True).")
        logger.warning("Strategy A (Real Data Fetch) is being skipped per configuration.")
        logger.info("Please run code/01_generate_synthetic.py for synthetic data generation.")
        return

    if not sra_accession:
        logger.error("No SRA accession ID found in config. Cannot proceed with real data fetch.")
        logger.error("Ensure T010 has set config.SRA_ACCESSION or verify data/research/sra_status.json.")
        raise ValueError("Missing SRA Accession ID in configuration.")

    otu_output_path = raw_path / "otutable.csv"
    serology_output_path = raw_path / "serology.csv"

    try:
        # Fetch OTU Table
        logger.info(f"Fetching OTU table for accession: {sra_accession}")
        otu_df = fetch_otu_table(sra_accession)
        
        if otu_df is None or otu_df.empty:
            raise DataUnavailableError(f"Fetched OTU table is empty for accession {sra_accession}")
        
        otu_df.to_csv(otu_output_path, index=False)
        logger.info(f"Successfully wrote OTU table to {otu_output_path}")

        # Fetch Serology Metadata
        logger.info(f"Fetching serology metadata for accession: {sra_accession}")
        serology_df = fetch_serology_metadata(sra_accession)

        if serology_df is None or serology_df.empty:
            raise DataUnavailableError(f"Fetched serology metadata is empty for accession {sra_accession}")

        serology_df.to_csv(serology_output_path, index=False)
        logger.info(f"Successfully wrote serology metadata to {serology_output_path}")

        logger.info("Strategy A completed successfully. Real data files generated.")

    except DataUnavailableError as e:
        logger.error(f"Data fetch failed: {str(e)}")
        logger.error("This is a blocking error for real data analysis. "
                    "If no real data exists, T010 should have set USE_SYNTHETIC_DATA=True.")
        raise
    except Exception as e:
        log_error_context(e)
        raise

if __name__ == "__main__":
    main()
