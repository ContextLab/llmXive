"""
Script to run the Manual Curator pipeline.
Ensures data/raw/manual_curated.csv is generated (or created empty if missing).
"""
import logging
import sys
from pathlib import Path
from src.ingestion.manual_curator import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Run the manual curator pipeline."""
    setup_logging("run_manual_curator", level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting manual curator pipeline...")
    df = run_pipeline()
    
    if df.empty:
        logger.warning("Manual curator produced no data. Proceeding with empty dataset.")
    else:
        logger.info(f"Manual curator successfully processed {len(df)} entries.")
    
    logger.info("Manual curator pipeline complete.")
    return df

if __name__ == "__main__":
    main()
