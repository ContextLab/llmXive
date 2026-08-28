"""
Finalize descriptors by merging uncertainty flags, saving the final dataset,
and updating the state file with the SHA-256 hash of the output.

This script implements Task T017:
- Loads the intermediate descriptors CSV from T014/T016.
- Loads uncertainty flags from T013c/T013b.
- Merges the `T_d_uncertainty` column into the final dataset.
- Saves the final `data/processed/descriptors.csv`.
- Updates `state/...yaml` with the artifact hash.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import from local modules based on provided API surface
from utils.state_manager import update_artifact_state, compute_sha256, load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

DESCRIPTORS_INPUT_PATH = PROCESSED_DIR / "descriptors_temp.csv" # Intermediate from T014/T015/T016
UNCERTAINTY_FLAGS_PATH = RAW_DIR / "uncertainty_flags.json"
FINAL_OUTPUT_PATH = PROCESSED_DIR / "descriptors.csv"
STATE_FILE_PATH = STATE_DIR / "artifacts.yaml"

# Note: If the previous pipeline stages wrote directly to descriptors.csv,
# we might need to adjust the input path. Assuming a temp file or the current
# state of descriptors.csv before finalization.
# Based on T014/T016, they write to data/processed/descriptors.csv.
# T017 needs to add the uncertainty column.
# So we read the current descriptors.csv (which lacks T_d_uncertainty),
# merge, and overwrite.
DESCRIPTORS_INPUT_PATH = PROCESSED_DIR / "descriptors.csv"

def load_descriptors() -> pd.DataFrame:
    """Load the intermediate descriptors dataframe."""
    if not DESCRIPTORS_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input descriptors file not found at {DESCRIPTORS_INPUT_PATH}. "
            "Please ensure T014 and T016 have been completed successfully."
        )
    df = pd.read_csv(DESCRIPTORS_INPUT_PATH)
    logger.info(f"Loaded {len(df)} rows from {DESCRIPTORS_INPUT_PATH}")
    return df

def load_uncertainty_flags() -> Dict[str, Any]:
    """Load the uncertainty flags mapping from JSON."""
    if not UNCERTAINTY_FLAGS_PATH.exists():
        raise FileNotFoundError(
            f"Uncertainty flags file not found at {UNCERTAINTY_FLAGS_PATH}. "
            "Please ensure T013c has been completed successfully."
        )
    with open(UNCERTAINTY_FLAGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded uncertainty flags from {UNCERTAINTY_FLAGS_PATH}")
    return data

def merge_uncertainty(df: pd.DataFrame, flags: Dict[str, Any]) -> pd.DataFrame:
    """
    Merge uncertainty data into the dataframe.
    Assumes flags is a dict where keys are entry IDs or indices,
    or a list of dicts with an ID matching the dataframe index or a specific column.
    
    Based on T013c, the flags likely contain the 'T_d_uncertainty' value for each entry.
    We expect the dataframe to have a unique identifier (e.g., 'id' or 'entry_id')
    or we map by index if the order is preserved.
    
    For robustness, we assume the JSON contains a list of records with 'id' and 'T_d_uncertainty'.
    """
    # Convert flags to a DataFrame for merging if it's a list of dicts
    if isinstance(flags, list):
        flags_df = pd.DataFrame(flags)
        if 'id' in flags_df.columns and 'T_d_uncertainty' in flags_df.columns:
            # Merge on 'id'
            if 'id' in df.columns:
                df = df.merge(flags_df[['id', 'T_d_uncertainty']], on='id', how='left')
            else:
                # Fallback: assume index alignment if no ID column, though less robust
                # This is a fallback if the previous stage didn't generate an ID column
                # but the flags were generated in the same order.
                # However, JSON usually implies a structure. Let's assume 'id' exists.
                # If 'id' is missing in df, we might need to use the index.
                # Let's try to map by index if no ID column exists.
                if len(flags) == len(df):
                    df['T_d_uncertainty'] = [f.get('T_d_uncertainty') for f in flags]
                else:
                    logger.warning("Index count mismatch and no 'id' column. Cannot merge uncertainty by index.")
                    # Try to find a common key if 'id' is not the key
                    common_keys = set(df.columns) & set(flags_df.columns)
                    if common_keys:
                        key = list(common_keys)[0]
                        df = df.merge(flags_df[['id', 'T_d_uncertainty']], left_on=key, right_on='id', how='left', suffixes=('', '_flag'))
                        df = df.drop(columns=['id_flag']) # Clean up
                    else:
                        raise ValueError("Cannot merge uncertainty: No common key found and index counts differ.")
        else:
            raise ValueError("Uncertainty flags JSON must contain 'id' and 'T_d_uncertainty' columns.")
    elif isinstance(flags, dict):
        # If it's a flat dict {id: uncertainty}
        if 'T_d_uncertainty' in flags:
            # Special case: single global uncertainty? Unlikely for per-entry.
            # Assuming it's a mapping {entry_id: uncertainty_value}
            # We need to map this to the dataframe.
            if 'id' in df.columns:
                df['T_d_uncertainty'] = df['id'].map(flags)
            else:
                raise ValueError("Cannot merge dict uncertainty flags: No 'id' column in dataframe.")
        else:
            # Maybe the dict is {entry_id: {uncertainty_key: value}}
            # Flatten it
            flat_flags = {}
            for k, v in flags.items():
                if isinstance(v, dict) and 'T_d_uncertainty' in v:
                    flat_flags[k] = v['T_d_uncertainty']
                else:
                    # Assume value is the uncertainty directly
                    flat_flags[k] = v
            
            if 'id' in df.columns:
                df['T_d_uncertainty'] = df['id'].map(flat_flags)
            else:
                raise ValueError("Cannot merge dict uncertainty flags: No 'id' column in dataframe.")
    
    # Check for missing merges
    missing = df['T_d_uncertainty'].isna().sum()
    if missing > 0:
        logger.warning(f"Found {missing} entries with missing T_d_uncertainty after merge.")
    
    return df

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """Save the final dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final descriptors to {output_path}")

def update_state(output_path: Path) -> str:
    """Compute SHA-256 of the output and update the state file."""
    artifact_hash = compute_sha256(output_path)
    logger.info(f"Computed SHA-256 hash: {artifact_hash}")
    
    state = load_state(STATE_FILE_PATH)
    update_artifact_state(state, output_path.name, artifact_hash)
    save_state(state, STATE_FILE_PATH)
    logger.info(f"Updated state file at {STATE_FILE_PATH}")
    
    return artifact_hash

def main() -> None:
    """Main execution flow for T017."""
    try:
        # 1. Load descriptors
        df = load_descriptors()
        
        # 2. Load uncertainty flags
        flags = load_uncertainty_flags()
        
        # 3. Merge uncertainty
        df_final = merge_uncertainty(df, flags)
        
        # 4. Ensure T_d_uncertainty column exists (even if all NaN, though it should be filled)
        if 'T_d_uncertainty' not in df_final.columns:
            logger.error("Final merge failed to produce 'T_d_uncertainty' column.")
            sys.exit(1)
        
        # 5. Save final dataset
        save_descriptors(df_final, FINAL_OUTPUT_PATH)
        
        # 6. Update state
        hash_value = update_state(FINAL_OUTPUT_PATH)
        
        logger.info(f"T017 completed successfully. Output: {FINAL_OUTPUT_PATH}, Hash: {hash_value}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T017 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
