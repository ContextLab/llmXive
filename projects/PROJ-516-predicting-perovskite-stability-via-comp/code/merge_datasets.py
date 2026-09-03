import logging
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd
from utils.state_manager import compute_sha256, update_artifact_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NREL_PATH = PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv"
MP_PATH = PROJECT_ROOT / "data" / "raw" / "mp_perovskites.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "perovskites_merged.csv"

def load_csv_safe(file_path: Path) -> pd.DataFrame:
    """
    Safely load a CSV file.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if the file is empty or has no rows.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Source file is empty or has no data rows: {file_path}")
    
    logger.info(f"Loaded {len(df)} rows from {file_path.name}")
    return df

def merge_perovskite_datasets() -> Tuple[pd.DataFrame, int]:
    """
    Merge NREL and Materials Project data.
    
    1. Verifies both source files exist and are non-empty (as per T012d constraint).
    2. Concatenates the DataFrames.
    3. Drops duplicates based on 'formula' and 'source'.
    4. Logs the count of removed duplicates.
    5. Writes the final merged dataset to data/raw/perovskites_merged.csv.
    
    Returns:
        Tuple[pd.DataFrame, int]: The merged DataFrame and the count of removed duplicates.
    
    Raises:
        FileNotFoundError: If either source file is missing.
        ValueError: If either source file is empty.
    """
    logger.info("Starting dataset merge process.")
    
    # 1. Load sources (fails loudly if missing/empty, satisfying T012d constraint)
    try:
        df_nrel = load_csv_safe(NREL_PATH)
        df_mp = load_csv_safe(MP_PATH)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Merge failed due to missing or invalid source data: {e}")
        raise

    # 2. Concatenate
    logger.info("Concatenating datasets...")
    merged_df = pd.concat([df_nrel, df_mp], ignore_index=True)
    initial_count = len(merged_df)
    logger.info(f"Total rows before deduplication: {initial_count}")

    # 3. Drop duplicates based on 'formula' and 'source'
    # Ensure 'source' column exists; if not, assume source based on filename context if needed,
    # but standard practice is to have a 'source' column.
    # If 'source' is missing in one, we might need to add it before concat.
    # Assuming T012a/T012b ensured 'source' column exists. If not, we add it here for safety.
    if 'source' not in merged_df.columns:
        logger.warning("'source' column missing in merged data. Attempting to infer...")
        # This should ideally be handled in fetchers, but fallback logic here:
        # We cannot reliably infer row-by-row without index, so we assume the fetchers did their job.
        # If this fails, the data is malformed.
        raise ValueError("Critical: 'source' column missing in input data. Fetchers must ensure this column exists.")

    if 'formula' not in merged_df.columns:
        raise ValueError("Critical: 'formula' column missing in input data.")

    # Drop duplicates
    # Keep the first occurrence
    merged_df.drop_duplicates(subset=['formula', 'source'], inplace=True)
    
    final_count = len(merged_df)
    duplicates_removed = initial_count - final_count

    logger.info(f"Total rows after deduplication: {final_count}")
    logger.info(f"Removed {duplicates_removed} duplicate entries based on 'formula' and 'source'.")

    # 4. Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Merged dataset written to {OUTPUT_PATH}")

    # 5. Update state
    try:
        sha_hash = compute_sha256(OUTPUT_PATH)
        update_artifact_state("perovskites_merged.csv", sha_hash)
        logger.info(f"State updated for {OUTPUT_PATH} with hash {sha_hash[:16]}...")
    except Exception as e:
        logger.warning(f"Failed to update state for merged dataset: {e}")

    return merged_df, duplicates_removed

def main():
    """Entry point for the merge script."""
    try:
        merged_df, dup_count = merge_perovskite_datasets()
        logger.info("Merge completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Merge process failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())