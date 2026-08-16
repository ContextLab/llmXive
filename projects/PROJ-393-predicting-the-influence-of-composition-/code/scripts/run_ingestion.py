"""
Script to run the Ingestion Pipeline.
Orchestrates fetching from NIST, Journal, and Manual sources.
"""
import logging
import sys
from pathlib import Path
from src.ingestion.ingest_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Run the ingestion pipeline."""
    setup_logging("run_ingestion", level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting ingestion pipeline...")
    df = run_pipeline()
    
    if df is None or df.empty:
        logger.warning("Ingestion pipeline produced no data. Proceeding with empty dataset.")
    else:
        logger.info(f"Ingestion pipeline successfully processed {len(df)} entries.")
    
    logger.info("Ingestion pipeline complete.")
    return df

if __name__ == "__main__":
    main()