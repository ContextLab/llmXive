"""
T017: Validation script to ensure confidence_summary.csv and accuracy_summary.csv
are derived from disjoint trial sets.

This script reads the two summary files, extracts the unique trial IDs used in each,
and verifies that the intersection is empty. It outputs a validation report to
data/validation/disjoint_trials_report.json.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_summary_file(filepath: Path) -> pd.DataFrame:
    """Load a summary CSV file and return it."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required summary file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Determine the trial ID column name
    possible_cols = ['trial_id', 'TrialID', 'trialID', 'id']
    trial_col = None
    for col in possible_cols:
        if col in df.columns:
            trial_col = col
            break
    
    if trial_col is None:
        # Fallback: assume the first column is the ID if it looks like an ID
        # or raise an error if we can't find a clear candidate
        if 'trial_id' not in df.columns and len(df.columns) > 0:
            # Check if any column contains 'trial' (case insensitive)
            trial_col = next((c for c in df.columns if 'trial' in c.lower()), None)
        
        if trial_col is None:
            raise ValueError(f"Could not identify trial ID column in {filepath}. "
                             f"Available columns: {list(df.columns)}")
    
    return df, trial_col

def get_unique_trials(df: pd.DataFrame, trial_col: str) -> set:
    """Extract unique trial IDs from a DataFrame."""
    return set(df[trial_col].dropna().unique())

def validate_disjoint(confidence_path: Path, accuracy_path: Path, output_path: Path) -> bool:
    """
    Validate that confidence_summary.csv and accuracy_summary.csv use disjoint trial sets.
    
    Returns True if validation passes, False otherwise.
    """
    logger.info(f"Loading confidence summary from: {confidence_path}")
    confidence_df, conf_col = load_summary_file(confidence_path)
    confidence_trials = get_unique_trials(confidence_df, conf_col)
    logger.info(f"Found {len(confidence_trials)} unique trials in confidence summary.")

    logger.info(f"Loading accuracy summary from: {accuracy_path}")
    accuracy_df, acc_col = load_summary_file(accuracy_path)
    accuracy_trials = get_unique_trials(accuracy_df, acc_col)
    logger.info(f"Found {len(accuracy_trials)} unique trials in accuracy summary.")

    # Check for intersection
    intersection = confidence_trials.intersection(accuracy_trials)
    is_disjoint = len(intersection) == 0

    report = {
        "status": "PASS" if is_disjoint else "FAIL",
        "confidence_summary_file": str(confidence_path),
        "accuracy_summary_file": str(accuracy_path),
        "confidence_trial_count": len(confidence_trials),
        "accuracy_trial_count": len(accuracy_trials),
        "intersection_count": len(intersection),
        "intersection_trials": sorted(list(intersection))[:20],  # Limit to first 20 if any
        "message": "Validation passed: Trial sets are disjoint." if is_disjoint 
                   else f"Validation failed: {len(intersection)} overlapping trials found."
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to: {output_path}")
    logger.info(report["message"])

    return is_disjoint

def main():
    """Main entry point for the validation script."""
    # Define paths relative to project root (assumed to be run from project root)
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    derived_dir = data_dir / "derived"
    validation_dir = data_dir / "validation"

    confidence_path = derived_dir / "confidence_summary.csv"
    accuracy_path = derived_dir / "accuracy_summary.csv"
    output_path = validation_dir / "disjoint_trials_report.json"

    logger.info("Starting disjoint trial validation (T017)...")

    try:
        success = validate_disjoint(confidence_path, accuracy_path, output_path)
        if success:
            logger.info("T017 Validation: SUCCESS")
            sys.exit(0)
        else:
            logger.error("T017 Validation: FAILED - Overlapping trials detected.")
            sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Ensure that T012 (preprocess) and subsequent analysis steps "
                     "have generated the required summary files.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
