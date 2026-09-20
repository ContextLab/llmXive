"""
T012c: Implement merge logic for perovskite datasets.

Concatenates NREL and Materials Project datasets based on formula and source.
Fails loudly if input files are missing or empty.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.state_manager import compute_sha256, update_artifact_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
NREL_PATH = PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv"
MP_PATH = PROJECT_ROOT / "data" / "raw" / "mp_perovskites.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "perovskites_merged.csv"
STATE_PATH = PROJECT_ROOT / "state" / "artifacts.yaml"


def load_csv_safe(filepath: Path) -> pd.DataFrame:
    """
    Load a CSV file safely.

    Args:
        filepath: Path to the CSV file.

    Returns:
        DataFrame containing the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    logger.info(f"Loading data from {filepath}...")
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV {filepath}: {e}")

    if df.empty:
        raise ValueError(f"Input file {filepath} is empty or contains no data rows.")

    logger.info(f"Loaded {len(df)} rows from {filepath.name}")
    return df


def merge_perovskite_datasets() -> Tuple[pd.DataFrame, int]:
    """
    Concatenate NREL and MP datasets and handle duplicates.

    Returns:
        Tuple of (merged DataFrame, count of removed duplicates).

    Raises:
        FileNotFoundError/ValueError: If inputs are missing or empty.
    """
    # Load inputs
    nrel_df = load_csv_safe(NREL_PATH)
    mp_df = load_csv_safe(MP_PATH)

    # Ensure 'source' column exists and is set correctly if missing
    # Assuming the fetch scripts might not have added 'source' explicitly
    # or if they did, we ensure consistency for the merge key.
    if 'source' not in nrel_df.columns:
        nrel_df['source'] = 'NREL'
    if 'source' not in mp_df.columns:
        mp_df['source'] = 'MaterialsProject'

    # Concatenate
    logger.info("Concatenating datasets...")
    merged_df = pd.concat([nrel_df, mp_df], ignore_index=True)

    # Identify duplicates based on 'formula' and 'source'
    # The task description says "based on formula and source".
    # Usually, duplicates in this context mean same formula from same source.
    # If the intention was to dedup same formula across sources, the logic would differ.
    # Given "concatenate... based on formula and source", we assume we want to keep
    # distinct entries for the same formula if they come from different sources,
    # but remove exact duplicates (same formula, same source).
    initial_count = len(merged_df)
    duplicate_mask = merged_df.duplicated(subset=['formula', 'source'], keep='first')
    duplicates_removed = merged_df[duplicate_mask]
    final_count = len(merged_df) - len(duplicates_removed)

    if len(duplicates_removed) > 0:
        logger.warning(f"Found {len(duplicates_removed)} duplicate entries (formula + source). Removing them.")
        merged_df = merged_df.drop_duplicates(subset=['formula', 'source'], keep='first')

    logger.info(f"Merged dataset size: {len(merged_df)} rows (removed {len(duplicates_removed)} duplicates).")

    return merged_df, len(duplicates_removed)


def main():
    """Main entry point for T012c."""
    try:
        merged_df, dup_count = merge_perovskite_datasets()

        # Write output
        logger.info(f"Writing merged data to {OUTPUT_PATH}...")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(OUTPUT_PATH, index=False)

        # Update state
        logger.info("Updating artifact state...")
        file_hash = compute_sha256(OUTPUT_PATH)
        update_artifact_state(
            artifact_path=OUTPUT_PATH,
            state_file=STATE_PATH,
            hash_value=file_hash
        )

        logger.info(f"T012c completed successfully. Output: {OUTPUT_PATH}, Duplicates removed: {dup_count}")

    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"T012c failed with input error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"T012c failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()