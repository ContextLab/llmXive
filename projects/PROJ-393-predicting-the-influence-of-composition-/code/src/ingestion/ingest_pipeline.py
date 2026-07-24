"""
Ingestion Pipeline Module.
Orchestrates fetching, parsing, and merging data from NIST, Journal, and Manual sources.
Saves the merged result to data/raw/merged_alloys.csv.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.ingestion.nist_fetcher import fetch_nist_data
from src.ingestion.journal_supplement_parser import fetch_journal_data
from src.ingestion.manual_curator import load_manual_curated_data
from src.utils.logging_config import setup_logging, create_logger
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
RAW_DATA_PATH = project_root / "data" / "raw"
MERGED_OUTPUT_PATH = RAW_DATA_PATH / "merged_alloys.csv"

def load_sources() -> List[pd.DataFrame]:
    """
    Load data from all configured sources.
    Returns a list of DataFrames.
    """
    sources = []
    
    # 1. NIST
    logger.info("Fetching NIST data...")
    nist_df = fetch_nist_data()
    if nist_df is not None and not nist_df.empty:
        sources.append(nist_df)
        logger.info(f"NIST source contributed {len(nist_df)} rows.")
    else:
        logger.warning("NIST source returned no data.")
    
    # 2. Journal
    logger.info("Fetching Journal data...")
    journal_df = fetch_journal_data()
    if journal_df is not None and not journal_df.empty:
        sources.append(journal_df)
        logger.info(f"Journal source contributed {len(journal_df)} rows.")
    else:
        logger.warning("Journal source returned no data.")
    
    # 3. Manual
    logger.info("Loading Manual data...")
    manual_df = load_manual_curated_data()
    if manual_df is not None and not manual_df.empty:
        sources.append(manual_df)
        logger.info(f"Manual source contributed {len(manual_df)} rows.")
    else:
        logger.warning("Manual source returned no data.")
    
    return sources

def merge_and_save(sources: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge source DataFrames and save to disk.
    """
    if not sources:
        logger.warning("No sources to merge. Creating empty merged file.")
        empty_df = pd.DataFrame(columns=[
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
            'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
        ])
        empty_df.to_csv(MERGED_OUTPUT_PATH, index=False)
        return empty_df
    
    # Concatenate
    merged_df = pd.concat(sources, ignore_index=True)
    
    # Ensure standard columns exist
    required_cols = [
        'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
        'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
    ]
    for col in required_cols:
        if col not in merged_df.columns:
            merged_df[col] = None
    
    # Reorder columns
    merged_df = merged_df[required_cols]
    
    # Save
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(MERGED_OUTPUT_PATH, index=False)
    logger.info(f"Merged data saved to {MERGED_OUTPUT_PATH} with {len(merged_df)} rows.")
    
    return merged_df

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Execute the full ingestion pipeline.
    """
    logger.info("Starting Ingestion Pipeline...")
    sources = load_sources()
    return merge_and_save(sources)

def main():
    """Entry point for the ingestion pipeline."""
    setup_logging()
    try:
        run_ingestion_pipeline()
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
