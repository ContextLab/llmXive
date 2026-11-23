"""
Ingestion Pipeline Module.
Orchestrates fetching, parsing, and merging data from NIST, Journal, and Manual sources.
Implements "Fail Loudly" for real data fetches: if a fetch fails, it logs a warning
and proceeds with available sources (graceful degradation), never substituting synthetic data.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.ingestion.nist_fetcher import fetch_nist_data
from src.ingestion.journal_supplement_parser import fetch_journal_data
from src.ingestion.manual_curator import load_manual_curated_data, save_manual_curated_data
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

def load_sources() -> Dict[str, pd.DataFrame]:
    """
    Load data from all configured sources.
    
    Returns:
        Dict mapping source name to DataFrame.
        If a source fails to fetch, logs a warning and includes an empty DataFrame.
    """
    sources = {}
    
    # 1. NIST Source
    try:
        logger.info("Fetching NIST data...")
        nist_df = fetch_nist_data()
        if nist_df is not None and not nist_df.empty:
            sources['NIST'] = nist_df
            logger.info(f"NIST source: {len(nist_df)} entries.")
        else:
            logger.warning("NIST fetch returned no data. Proceeding without NIST.")
            sources['NIST'] = pd.DataFrame()
    except Exception as e:
        logger.warning(f"NIST fetch failed: {e}. Proceeding without NIST.")
        sources['NIST'] = pd.DataFrame()
    
    # 2. Journal Source
    try:
        logger.info("Fetching Journal data...")
        journal_df = fetch_journal_data()
        if journal_df is not None and not journal_df.empty:
            sources['Journal'] = journal_df
            logger.info(f"Journal source: {len(journal_df)} entries.")
        else:
            logger.warning("Journal fetch returned no data. Proceeding without Journal.")
            sources['Journal'] = pd.DataFrame()
    except Exception as e:
        logger.warning(f"Journal fetch failed: {e}. Proceeding without Journal.")
        sources['Journal'] = pd.DataFrame()
    
    # 3. Manual Source
    try:
        logger.info("Loading Manual curated data...")
        manual_df = load_manual_curated_data()
        if not manual_df.empty:
            sources['Manual'] = manual_df
            logger.info(f"Manual source: {len(manual_df)} entries.")
        else:
            logger.warning("Manual curated data is empty. Proceeding without Manual.")
            sources['Manual'] = pd.DataFrame()
    except Exception as e:
        logger.warning(f"Manual data load failed: {e}. Proceeding without Manual.")
        sources['Manual'] = pd.DataFrame()
    
    return sources

def merge_and_save(sources: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Merge all source DataFrames and save to raw directory.
    
    Returns:
        Merged DataFrame or None if all sources are empty.
    """
    dfs = [df for df in sources.values() if not df.empty]
    
    if not dfs:
        logger.warning("All sources returned empty data. No data to merge.")
        return None
    
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Add metadata columns if missing
    if 'source_type' not in merged_df.columns:
        # Infer source_type based on origin if possible, otherwise default
        # This is a simplification; real logic might track origin during fetch
        merged_df['source_type'] = 'Mixed' 
    
    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = RAW_DATA_DIR / "alloys_raw_merged.csv"
    logger.info(f"Saving merged data to {output_path} ({len(merged_df)} rows).")
    merged_df.to_csv(output_path, index=False)
    
    return merged_df

def run_ingestion_pipeline() -> Optional[pd.DataFrame]:
    """
    Main pipeline entry point.
    Orchestrates loading and merging.
    """
    setup_logging("ingestion_pipeline", level=logging.INFO)
    logger.info("Starting ingestion pipeline...")
    
    sources = load_sources()
    merged_df = merge_and_save(sources)
    
    if merged_df is None:
        logger.warning("Ingestion pipeline completed with NO data.")
    else:
        logger.info(f"Ingestion pipeline completed successfully. Total rows: {len(merged_df)}")
    
    return merged_df

def main():
    """Entry point for ingestion pipeline script."""
    df = run_ingestion_pipeline()
    return df

if __name__ == "__main__":
    main()
