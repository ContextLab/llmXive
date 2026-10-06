"""
Merge datasets from NREL and Materials Project sources into a single CSV.

This script implements T012c and T012e:
1. Loads nrel_perovskites.csv and mp_perovskites.csv
2. Concatenates them (keeping separate rows for matching formulas from different sources)
3. Removes duplicates based on formula AND source
4. Writes the final merged dataset to data/raw/perovskites_merged.csv
"""
import logging
import sys
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/merge_operations.log')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
NREL_PATH = DATA_RAW_DIR / "nrel_perovskites.csv"
MP_PATH = DATA_RAW_DIR / "mp_perovskites.csv"
MERGED_PATH = DATA_RAW_DIR / "perovskites_merged.csv"

def load_csv_safe(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file. Returns None if file is missing or empty.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame or None if file is missing/empty
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.error(f"File is empty: {file_path}")
            return None
        logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def merge_perovskite_datasets(nrel_df: pd.DataFrame, mp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Concatenate NREL and MP datasets.
    
    Constraint: If rows have matching `formula` but different `source`, 
    keep them as separate rows (do not merge).
    
    Args:
        nrel_df: DataFrame from NREL source
        mp_df: DataFrame from Materials Project source
        
    Returns:
        Concatenated DataFrame
    """
    logger.info("Concatenating datasets...")
    combined_df = pd.concat([nrel_df, mp_df], ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} rows before deduplication")
    return combined_df

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop duplicates based on `formula` AND `source`.
    
    Constraint: Use standard deduplication logic (formula + source match).
    Log the count of removed duplicates.
    
    Args:
        df: DataFrame to deduplicate
        
    Returns:
        Deduplicated DataFrame
    """
    logger.info("Removing duplicates based on formula and source...")
    initial_count = len(df)
    df_deduped = df.drop_duplicates(subset=['formula', 'source'], keep='first')
    removed_count = initial_count - len(df_deduped)
    logger.info(f"Removed {removed_count} duplicate rows. Final count: {len(df_deduped)}")
    return df_deduped

def main():
    """
    Main execution function for T012c and T012e.
    
    Steps:
    1. Load nrel_perovskites.csv
    2. Load mp_perovskites.csv
    3. Fail if either is missing, empty, or if upstream tasks failed
    4. Merge datasets
    5. Remove duplicates
    6. Write to data/raw/perovskites_merged.csv
    7. Log final row count
    """
    logger.info("Starting merge and deduplication process (T012c/T012e)...")
    
    # Load source files
    nrel_df = load_csv_safe(NREL_PATH)
    mp_df = load_csv_safe(MP_PATH)
    
    # Fail if inputs are missing or empty (per task constraint)
    if nrel_df is None:
        logger.error("T012c/T012e FAILED: nrel_perovskites.csv is missing or empty.")
        sys.exit(1)
    if mp_df is None:
        logger.error("T012c/T012e FAILED: mp_perovskites.csv is missing or empty.")
        sys.exit(1)
    
    # Merge datasets
    merged_df = merge_perovskite_datasets(nrel_df, mp_df)
    
    # Remove duplicates
    final_df = remove_duplicates(merged_df)
    
    # Ensure output directory exists
    MERGED_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write final merged dataset
    final_df.to_csv(MERGED_PATH, index=False)
    logger.info(f"Final merged dataset written to {MERGED_PATH}")
    logger.info(f"Final row count: {len(final_df)}")
    
    # Verify output
    if not MERGED_PATH.exists():
        logger.error("CRITICAL: Output file was not created.")
        sys.exit(1)
        
    logger.info("T012c/T012e completed successfully.")

if __name__ == "__main__":
    main()