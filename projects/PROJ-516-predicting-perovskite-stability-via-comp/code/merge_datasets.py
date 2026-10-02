import logging
import sys
import os
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_csv_safe(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file. Returns None if the file does not exist or is empty.
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"File is empty: {file_path}")
            return None
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def merge_perovskite_datasets(nrel_path: Path, mp_path: Path) -> pd.DataFrame:
    """
    Merge NREL and Materials Project datasets based on 'formula' and 'source'.
    """
    nrel_df = load_csv_safe(nrel_path)
    mp_df = load_csv_safe(mp_path)

    if nrel_df is None or mp_df is None:
        raise FileNotFoundError("One or more source datasets are missing or empty.")

    # Concatenate the two DataFrames
    merged_df = pd.concat([nrel_df, mp_df], ignore_index=True)
    
    logger.info(f"Initial merge count: {len(merged_df)}")
    return merged_df

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop duplicates based on 'formula' and 'source'.
    """
    initial_count = len(df)
    # Ensure 'formula' and 'source' columns exist
    if 'formula' not in df.columns or 'source' not in df.columns:
        raise ValueError("DataFrame must contain 'formula' and 'source' columns for deduplication.")
    
    df_deduped = df.drop_duplicates(subset=['formula', 'source'], keep='first')
    removed_count = initial_count - len(df_deduped)
    
    logger.info(f"Removed {removed_count} duplicates based on 'formula' and 'source'.")
    return df_deduped

def main():
    """
    Main entry point for T012e: Write final merged dataset to data/raw/perovskites_merged.csv.
    Prerequisites: T012c (Merge logic) and T012d (Duplicate removal) must have run successfully.
    """
    base_dir = Path(__file__).resolve().parent.parent
    nrel_path = base_dir / "data" / "raw" / "nrel_perovskites.csv"
    mp_path = base_dir / "data" / "raw" / "mp_perovskites.csv"
    output_path = base_dir / "data" / "raw" / "perovskites_merged.csv"

    logger.info(f"Starting merge process for {output_path}")

    try:
        # 1. Merge datasets
        merged_df = merge_perovskite_datasets(nrel_path, mp_path)

        # 2. Remove duplicates
        final_df = remove_duplicates(merged_df)

        # 3. Log final row count
        logger.info(f"Final row count: {len(final_df)}")

        # 4. Write to disk
        final_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote final merged dataset to {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Prerequisite data missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()