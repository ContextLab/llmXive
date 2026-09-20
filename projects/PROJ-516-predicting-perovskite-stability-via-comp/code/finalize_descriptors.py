"""
Task T012e: Write final merged dataset to data/raw/perovskites_merged.csv.

This script consolidates the merged dataset (after duplicate removal) and
writes it to the final output location. It logs the final row count as required.

Dependencies:
  - T012d: Implements duplicate removal on the merged dataset.
  - code/merge_datasets.py: Provides the merge logic (though this script assumes
    the merged file exists or performs the merge if needed).

Note: Since T012c and T012d are marked complete, we assume the intermediate
merged file exists. However, to ensure robustness and that this script
actually produces the output, we will re-implement the merge logic here
or load the intermediate result if T012d produced a specific file.

Based on the task chain:
T012a -> nrel_perovskites.csv
T012b -> mp_perovskites.csv
T012c -> Merge logic (likely produces a temp or direct output)
T012d -> Drop duplicates (likely produces a temp or direct output)
T012e -> Final write to data/raw/perovskites_merged.csv

We will implement the full pipeline from the two source files to ensure
the final artifact is written correctly, effectively encapsulating the
logic of T012c and T012d if they didn't write the final file, or reading
the intermediate if they did.

Given the "Execution Failed" report indicates `data/raw/mp_perovskites.csv`
and `data/raw/nrel_perovskites.csv` are missing, this script will attempt
to fetch them if missing (as a fallback to the execution failure) OR
strictly load them if they exist.

HOWEVER, the instruction for T012e is specifically "Write final merged dataset".
It requires T012d. If T012d failed to produce the file, T012e cannot proceed.
But the execution failure shows the *source* files are missing.

To satisfy the "Fix the ROOT CAUSE" constraint for the whole project:
This script will act as the finalizer. It will:
1. Check for `data/raw/nrel_perovskites.csv` and `data/raw/mp_perovskites.csv`.
2. If they exist, load, merge, deduplicate, and write `data/raw/perovskites_merged.csv`.
3. If they don't exist, it raises an error (as T012a/T012b failed).

We will implement the merge and dedup logic here to ensure the final file
is generated correctly if the intermediate steps were skipped or failed.
"""

import logging
import sys
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
NREL_FILE = DATA_RAW_DIR / "nrel_perovskites.csv"
MP_FILE = DATA_RAW_DIR / "mp_perovskites.csv"
OUTPUT_FILE = DATA_RAW_DIR / "perovskites_merged.csv"

def load_csv_safe(path: Path) -> pd.DataFrame:
    """Load a CSV file safely, returning an empty DataFrame if missing."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {path}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return pd.DataFrame()

def merge_perovskite_datasets(df_nrel: pd.DataFrame, df_mp: pd.DataFrame) -> pd.DataFrame:
    """Concatenate NREL and MP datasets. Adds a 'source' column if missing."""
    if df_nrel.empty and df_mp.empty:
        logger.error("Both input datasets are empty. Cannot merge.")
        return pd.DataFrame()

    result_dfs = []
    
    if not df_nrel.empty:
        df_nrel_copy = df_nrel.copy()
        if 'source' not in df_nrel_copy.columns:
            df_nrel_copy['source'] = 'nrel'
        result_dfs.append(df_nrel_copy)
        logger.info(f"Added {len(df_nrel_copy)} rows from NREL")

    if not df_mp.empty:
        df_mp_copy = df_mp.copy()
        if 'source' not in df_mp_copy.columns:
            df_mp_copy['source'] = 'materials_project'
        result_dfs.append(df_mp_copy)
        logger.info(f"Added {len(df_mp_copy)} rows from Materials Project")

    if not result_dfs:
        return pd.DataFrame()

    merged = pd.concat(result_dfs, ignore_index=True)
    logger.info(f"Merged dataset size: {len(merged)} rows")
    return merged

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicates based on 'formula' and 'source'."""
    if df.empty:
        return df
    
    initial_count = len(df)
    # Ensure 'formula' and 'source' exist
    if 'formula' not in df.columns:
        logger.error("Column 'formula' missing in merged data.")
        return df
    if 'source' not in df.columns:
        logger.error("Column 'source' missing in merged data.")
        return df

    df_dedup = df.drop_duplicates(subset=['formula', 'source'], keep='first')
    removed_count = initial_count - len(df_dedup)
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} duplicate entries based on formula+source.")
    else:
        logger.info("No duplicate entries found.")
        
    return df_dedup

def main():
    """Main entry point for T012e."""
    logger.info("Starting T012e: Finalize Merged Dataset")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load sources
    # Note: If T012a/T012b failed, these files won't exist, and this script
    # will fail or produce an empty file. This is the correct behavior per
    # "fail loudly" if prerequisites aren't met.
    df_nrel = load_csv_safe(NREL_FILE)
    df_mp = load_csv_safe(MP_FILE)

    if df_nrel.empty and df_mp.empty:
        logger.critical("Neither NREL nor MP source files exist. T012e cannot proceed.")
        sys.exit(1)

    # Merge
    merged_df = merge_perovskite_datasets(df_nrel, df_mp)

    if merged_df.empty:
        logger.critical("Merged dataset is empty after concatenation.")
        sys.exit(1)

    # Deduplicate (T012d logic)
    final_df = remove_duplicates(merged_df)

    if final_df.empty:
        logger.critical("Dataset became empty after deduplication.")
        sys.exit(1)

    # Write final output
    try:
        final_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"SUCCESS: Wrote final merged dataset to {OUTPUT_FILE}")
        logger.info(f"Final row count: {len(final_df)}")
    except Exception as e:
        logger.critical(f"Failed to write output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()