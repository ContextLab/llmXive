import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)

def is_dft_entry(row: pd.Series) -> bool:
    """Check if a row is a DFT/Simulation entry."""
    # Check source_type
    source = str(row.get('source_type', '')).lower()
    if 'dft' in source or 'calculated' in source or 'simulation' in source:
        return True
    
    # Check other potential columns
    for col in row.index:
        val = str(row[col]).lower()
        if 'dft' in val or 'calculated' in val or 'simulation' in val or 'materials project' in val:
            return True
    
    return False

def filter_dft_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out DFT entries and log them."""
    if df.empty:
        return df
    
    logger.info("Filtering DFT entries...")
    initial_count = len(df)
    
    # Identify DFT rows
    dft_mask = df.apply(is_dft_entry, axis=1)
    dft_rows = df[dft_mask]
    non_dft_rows = df[~dft_mask]
    
    if not dft_rows.empty:
        logger.warning(f"Removing {len(dft_rows)} DFT/Simulation entries.")
        for idx, row in dft_rows.iterrows():
            logger.debug(f"Filtered DFT entry: {row.get('composition', 'Unknown')}")
    
    logger.info(f"Filter complete. Remaining rows: {len(non_dft_rows)}")
    return non_dft_rows.reset_index(drop=True)

def main():
    setup_logging()
    logger.info("DFT Filter Main Entry")
    return 0

if __name__ == "__main__":
    sys.exit(main())