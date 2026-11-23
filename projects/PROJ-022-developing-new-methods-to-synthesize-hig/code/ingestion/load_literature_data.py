"""
Loads and merges data from manual and automated sources.
"""
import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from ingestion.automated_fetch import (
    fetch_arxiv_membrane_papers,
    fetch_openpolymer_data,
    load_manual_extraction_data
)

logger = logging.getLogger(__name__)

def load_and_merge_sources() -> Optional[pd.DataFrame]:
    """
    Loads data from all configured sources and merges them into a single DataFrame.
    """
    sources = []
    
    # 1. Manual Extraction
    logger.info("Loading manual extraction data...")
    manual_df = load_manual_extraction_data()
    if manual_df is not None and not manual_df.empty:
        manual_df['source'] = 'manual'
        sources.append(manual_df)
        logger.info(f"Loaded {len(manual_df)} records from manual extraction.")
    
    # 2. Automated Fetch (OpenPolymer)
    logger.info("Fetching OpenPolymer data...")
    try:
        openpolymer_df = fetch_openpolymer_data()
        if openpolymer_df is not None and not openpolymer_df.empty:
            openpolymer_df['source'] = 'openpolymer'
            sources.append(openpolymer_df)
            logger.info(f"Loaded {len(openpolymer_df)} records from OpenPolymer.")
    except Exception as e:
        logger.warning(f"Failed to fetch OpenPolymer data: {e}")
    
    # 3. Automated Fetch (ArXiv - Note: ArXiv fetch might return papers, not structured data)
    # Assuming fetch_arxiv_membrane_papers returns a dataframe of extracted data or None
    logger.info("Fetching ArXiv data...")
    try:
        arxiv_df = fetch_arxiv_membrane_papers()
        if arxiv_df is not None and not arxiv_df.empty:
            arxiv_df['source'] = 'arxiv'
            sources.append(arxiv_df)
            logger.info(f"Loaded {len(arxiv_df)} records from ArXiv.")
    except Exception as e:
        logger.warning(f"Failed to fetch ArXiv data: {e}")

    if not sources:
        logger.error("No data sources were successfully loaded.")
        return None

    # Merge
    merged_df = pd.concat(sources, ignore_index=True)
    
    # Ensure required columns exist (fill with NaN if missing)
    required_cols = ['polymer_name', 'smiles', 'permeability', 'permeability_unit', 'selectivity']
    for col in required_cols:
        if col not in merged_df.columns:
            merged_df[col] = None
            
    return merged_df

def main():
    df = load_and_merge_sources()
    if df is not None:
        print(f"Successfully merged {len(df)} records.")
        print(df.head())
    else:
        print("Failed to load any data.")

if __name__ == "__main__":
    main()
