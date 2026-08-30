"""
finalize_descriptors.py

Task T017: Write final processed dataset to data/processed/descriptors.csv
including the T_d_uncertainty and perovskite_family columns and update
state/...yaml with hash.

This script aggregates the descriptor data with the computed uncertainties
and family classifications, performs a final validation, saves the CSV,
and updates the project state file with the SHA-256 hash of the output.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import from existing API surface
from utils.state_manager import compute_sha256, update_artifact_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"

# Output file paths
DESCRIPTORS_CSV = DATA_PROCESSED_DIR / "descriptors.csv"
UNCERTAINTY_FLAGS_FILE = DATA_RAW_DIR / "uncertainty_flags.json"
PEROVSKITE_FAMILY_FILE = DATA_PROCESSED_DIR / "perovskite_family.csv" # Assumed intermediate or same source
# Note: T014b output is expected to be integrated. If T014b writes to descriptors directly, we read from there.
# Based on T014b description: "write to data/processed/descriptors.csv".
# Based on T013b description: "write T_d_uncertainty column to data/processed/descriptors.csv".
# We assume T014 and T013b have populated a base descriptors.csv, and we are finalizing it.
# However, to be safe and follow the "merge" pattern of T017, we will attempt to load the base
# and the specific additions if they are separate, or just load the main one if already merged.
# The task says "Write final processed dataset... including...".
# Let's assume the base descriptors.csv exists from T014/T015, and we need to ensure
# T_d_uncertainty and perovskite_family are present and valid.

# If T014b and T013b wrote to the same file, we just need to verify and hash.
# But often in pipelines, these might be separate intermediate files or the task implies
# ensuring the final state.
# Let's assume the following workflow for T017:
# 1. Load the main descriptors.csv (from T014/T015).
# 2. Load uncertainty flags (from T013) if not already merged.
# 3. Load perovskite family (from T014b) if not already merged.
# 4. Merge/Ensure columns exist.
# 5. Save final CSV.
# 6. Update state.

# Check for intermediate files that might need merging
# If T013b and T014b wrote directly to descriptors.csv, we just verify.
# If they wrote to separate files, we merge.
# Given T013b: "write T_d_uncertainty column to data/processed/descriptors.csv"
# Given T014b: "write to data/processed/descriptors.csv"
# It implies they are modifying the same file.
# However, to be robust, we will check if the columns exist. If not, we look for backup sources.
# But the strict requirement is to produce the FINAL file.

# Let's assume the previous tasks have produced a base file, and we are finalizing it.
# If the file doesn't exist yet, we might need to construct it from T014 output + T013b + T014b.
# But T014 is not completed (it's T014b and T014 is pending? No, T014 is pending in the list?
# Wait, T014 is [~] (pending/failed?) in the list?
# T014: [~] T014 [US1] Implement code/feature_engineering.py...
# T014b: [X] T014b [US1] Implement logic to derive perovskite_family...
# T013b: [X] T013b [US1] Implement logic to extract temperature_precision...
# T015: [X] T015 [US1] Implement logic to exclude entries...
# T016: [X] T016 [US1] Implement VIF...
# T017: [ ] T017 [US1] Write final processed dataset...

# It seems T014 (the main feature engineering) might be the one that produces the base descriptors.csv.
# T014 is marked [~] which usually means "in progress" or "failed" in some systems, but here it's likely "pending" or "needs redo".
# However, T014b and T013b are marked [X] (completed).
# If T014 is not done, how do we have descriptors.csv?
# The prompt says "completed task ids" includes T014b and T013b, but NOT T014.
# This implies T014b and T013b might have written to a file that T014 would have also written to, or they wrote to a temporary file.
# OR, T014 is actually done but the list is just showing status.
# Let's assume the file `data/processed/descriptors.csv` exists from the previous steps (T013b/T014b) or we need to load the raw/merged data and recompute?
# No, T017 is "Write final processed dataset".
# Let's assume the file `data/processed/descriptors.csv` exists with the base features, and T013b/T014b have added their columns.
# If T014 is missing, we might not have the base features.
# But T014b says "derive perovskite_family ... from A/B/X site elements in T014 output".
# This implies T014 output exists.
# Let's assume the file `data/processed/descriptors.csv` is the current state.

# Strategy:
# 1. Try to load `data/processed/descriptors.csv`.
# 2. If it exists, check for required columns: `T_d_uncertainty`, `perovskite_family`.
# 3. If missing, look for intermediate files (e.g., `uncertainty_flags.json`, `perovskite_family.csv` if T014b wrote separately).
#    However, T013b says "write T_d_uncertainty column to data/processed/descriptors.csv".
#    T014b says "write to data/processed/descriptors.csv".
#    So they should be there.
# 4. If the file is missing entirely, we must reconstruct it from `data/raw/perovskites_merged.csv` and the intermediate JSONs?
#    But T014 (feature engineering) is the one that computes atomic fractions etc.
#    If T014 is not done, we cannot proceed.
#    However, the task list shows T014 as `[~]` (maybe "needs attention" or "in progress").
#    But T017 is the next task.
#    Let's assume for the sake of T017 that the file `data/processed/descriptors.csv` exists with the necessary columns,
#    or we are expected to finalize the file that T013b and T014b have been writing to.
#    If T014 is truly missing, T017 cannot run.
#    But the instruction says "Implement task T017".
#    I will assume the file exists and contains the data from T013b and T014b.
#    If not, I will try to load the raw data and the intermediate JSONs to reconstruct the necessary columns,
#    assuming T014's output (the base descriptors) is also present or can be inferred.
#    Actually, T014 is the one that computes "atomic fractions, weighted averages".
#    If T014 is not done, we don't have the base descriptors.
#    Wait, T014 is in the "Implementation for User Story 1" section.
#    T014b depends on T014.
#    If T014 is not done, T014b cannot be done.
#    But T014b is marked [X]. This implies T014 is effectively done or T014b did the work.
#    Let's assume `data/processed/descriptors.csv` exists and has the columns.

# If the file does not exist, we cannot complete T017.
# I will write the code to load, verify, and save.

def load_descriptors() -> pd.DataFrame:
    """Load the descriptors CSV file."""
    if not DESCRIPTORS_CSV.exists():
        logger.error(f"Descriptors file not found: {DESCRIPTORS_CSV}")
        # Attempt to load from raw if processed is missing? No, T014 should have created it.
        # If T014 is missing, we might need to run T014 logic here?
        # But T017 is just "Write final processed dataset".
        # Let's assume it exists.
        raise FileNotFoundError(f"Descriptors file not found: {DESCRIPTORS_CSV}")
    
    df = pd.read_csv(DESCRIPTORS_CSV)
    return df

def load_uncertainty_flags() -> Dict[str, Any]:
    """Load uncertainty flags from JSON."""
    if not UNCERTAINTY_FLAGS_FILE.exists():
        logger.warning(f"Uncertainty flags file not found: {UNCERTAINTY_FLAGS_FILE}")
        return {}
    with open(UNCERTAINTY_FLAGS_FILE, 'r') as f:
        return json.load(f)

def load_perovskite_family_data() -> Optional[pd.DataFrame]:
    """Load perovskite family data if stored separately, otherwise return None."""
    # T014b says "write to data/processed/descriptors.csv".
    # So it should be in the main file.
    # But if T014b wrote to a separate file for some reason, check here.
    # No specific file mentioned for T014b output other than descriptors.csv.
    return None

def merge_uncertainty(df: pd.DataFrame, uncertainty_data: Dict[str, Any]) -> pd.DataFrame:
    """Merge uncertainty data into the dataframe if not already present."""
    # Check if T_d_uncertainty column exists
    if 'T_d_uncertainty' not in df.columns:
        logger.info("Merging T_d_uncertainty column from uncertainty flags.")
        # Assuming uncertainty_data is a dict mapping formula to uncertainty
        # or a list of dicts. T013b says "write T_d_uncertainty column".
        # If it's missing, we try to reconstruct from the flags.
        # This is a fallback. Ideally, T013b already did this.
        if uncertainty_data:
            # Convert to series if possible
            # Assuming structure: { "formula": "sigma", ... }
            # We need to align by formula
            if isinstance(uncertainty_data, dict):
                # Check if keys are formulas
                # We need to map formula -> sigma
                # But df might have multiple columns for formula?
                # Usually 'formula' is a column.
                if 'formula' in df.columns:
                    df['T_d_uncertainty'] = df['formula'].map(uncertainty_data)
                    # Fill NaN with default if needed? T013b says "calculate sigma".
                    # If missing, T042 says default to 10.
                    # But T013b says "calculate sigma using T043".
                    # Let's assume the values are there.
                else:
                    logger.error("Cannot merge uncertainty: 'formula' column not found.")
            else:
                logger.warning("Uncertainty data format not recognized for merging.")
        else:
            logger.error("No uncertainty data available to merge.")
    return df

def ensure_perovskite_family(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure perovskite_family column exists."""
    if 'perovskite_family' not in df.columns:
        logger.warning("perovskite_family column not found. Attempting to load from separate source or recompute?")
        # T014b should have done this.
        # If T014b wrote to a separate file, we load it.
        # But T014b description says "write to data/processed/descriptors.csv".
        # So it should be there.
        # If not, we might need to recompute from A/B/X sites if those columns exist.
        # But T014b logic is complex.
        # Let's assume it's there.
        raise ValueError("perovskite_family column missing from descriptors.csv")
    return df

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """Save the final descriptors dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final descriptors to {output_path}")

def update_state(output_path: Path) -> None:
    """Update the state file with the hash of the output."""
    if not output_path.exists():
        logger.error(f"Cannot update state: file {output_path} does not exist.")
        return
    
    hash_value = compute_sha256(output_path)
    logger.info(f"Computed SHA-256 for {output_path}: {hash_value}")
    
    # Update state for the specific artifact
    update_artifact_state(
        artifact_path=str(output_path.relative_to(PROJECT_ROOT)),
        hash_value=hash_value,
        state_dir=STATE_DIR
    )
    logger.info(f"State updated for {output_path}")

def main() -> int:
    """Main entry point for T017."""
    try:
        # 1. Load descriptors
        df = load_descriptors()
        logger.info(f"Loaded {len(df)} rows from {DESCRIPTORS_CSV}")

        # 2. Load uncertainty flags
        uncertainty_data = load_uncertainty_flags()

        # 3. Merge uncertainty if needed
        df = merge_uncertainty(df, uncertainty_data)

        # 4. Ensure perovskite_family column
        df = ensure_perovskite_family(df)

        # 5. Validate required columns
        required_cols = ['T_d_uncertainty', 'perovskite_family']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return 1

        # 6. Save final dataset
        save_descriptors(df, DESCRIPTORS_CSV)

        # 7. Update state
        update_state(DESCRIPTORS_CSV)

        logger.info("T017 completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Error in T017: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
