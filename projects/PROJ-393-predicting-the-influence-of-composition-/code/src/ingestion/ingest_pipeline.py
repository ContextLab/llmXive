import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.ingestion.nist_fetcher import fetch_nist_data
from src.ingestion.manual_curator import load_manual_curated_data
# Import journal fetcher if it exists in the project, otherwise mock for safety
try:
    from src.ingestion.journal_supplement_parser import fetch_journal_data
except ImportError:
    def fetch_journal_data():
        logger = logging.getLogger(__name__)
        logger.warning("Journal supplement parser not found. Returning empty DataFrame.")
        return pd.DataFrame()

from src.utils.logging_config import setup_logging, create_logger
from src.utils.checksums import calculate_file_sha256
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
OUTPUT_DIR = project_root / "data" / "raw"
MERGED_OUTPUT = OUTPUT_DIR / "merged_sources.csv"

def load_sources() -> Dict[str, pd.DataFrame]:
    """Load data from all configured sources."""
    sources = {}
    
    # 1. NIST
    logger.info("Fetching NIST data...")
    nist_df = fetch_nist_data()
    if nist_df is not None and not nist_df.empty:
        nist_df['source_type'] = 'NIST'
        sources['NIST'] = nist_df
        logger.info(f"NIST data loaded: {len(nist_df)} rows")
    else:
        logger.warning("NIST data empty or failed.")
    
    # 2. Journal
    logger.info("Fetching Journal data...")
    journal_df = fetch_journal_data()
    if journal_df is not None and not journal_df.empty:
        journal_df['source_type'] = 'Journal'
        sources['Journal'] = journal_df
        logger.info(f"Journal data loaded: {len(journal_df)} rows")
    else:
        logger.warning("Journal data empty or failed.")
    
    # 3. Manual
    logger.info("Loading Manual data...")
    manual_df = load_manual_curated_data()
    if manual_df is not None and not manual_df.empty:
        manual_df['source_type'] = 'Manual'
        sources['Manual'] = manual_df
        logger.info(f"Manual data loaded: {len(manual_df)} rows")
    else:
        logger.warning("Manual data empty or failed.")
    
    return sources

def merge_and_save(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all source DataFrames and save to merged_sources.csv."""
    if not sources:
        logger.warning("No sources provided. Creating empty merged file.")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        empty_df = pd.DataFrame()
        empty_df.to_csv(MERGED_OUTPUT, index=False)
        return empty_df
    
    logger.info(f"Merging {len(sources)} sources...")
    df_list = list(sources.values())
    merged_df = pd.concat(df_list, ignore_index=True)
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(MERGED_OUTPUT, index=False)
    checksum = calculate_file_sha256(MERGED_OUTPUT)
    logger.info(f"Merged data saved to {MERGED_OUTPUT} ({len(merged_df)} rows). SHA256: {checksum}")
    
    return merged_df

def run_ingestion_pipeline() -> pd.DataFrame:
    """Orchestrate the full ingestion pipeline."""
    logger.info("Starting Ingestion Pipeline (T026)...")
    sources = load_sources()
    merged_df = merge_and_save(sources)
    logger.info("Ingestion Pipeline completed.")
    return merged_df

def main():
    setup_logging()
    logger.info("Ingestion Pipeline Main Entry")
    try:
        df = run_ingestion_pipeline()
        logger.info(f"Ingestion finished. Total rows: {len(df)}")
        return 0
    except Exception as e:
        logger.critical(f"Ingestion pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())