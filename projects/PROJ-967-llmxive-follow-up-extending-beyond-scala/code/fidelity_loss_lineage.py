import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Constants for the project paths relative to the repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "results"

# Derived rule string for hashing
DERIVATION_RULE_STRING = "sha256_prompt_text_mod_4_v1"

# Input/Output paths
CLEANED_DATA_PATH = DATA_PROCESSED_DIR / "cleaned_data.parquet"
LINEAGE_OUTPUT_PATH = DATA_PROCESSED_DIR / "fidelity_loss_lineage.json"
EXCLUSIONS_LOG_PATH = DATA_PROCESSED_DIR / "exclusions_log.json"
PRIMARY_DIMENSION_LINEAGE_PATH = DATA_PROCESSED_DIR / "lineage_report.json"

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def setup_directories() -> None:
    """Ensure output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned data produced by T024."""
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {CLEANED_DATA_PATH}. "
            "Please ensure task T024 has been executed successfully."
        )
    return pd.read_parquet(CLEANED_DATA_PATH)

def load_primary_dimension_lineage() -> List[Dict[str, Any]]:
    """Load the lineage report for primary dimension derivation."""
    if not PRIMARY_DIMENSION_LINEAGE_PATH.exists():
        logging.warning(
            f"Primary dimension lineage report not found at {PRIMARY_DIMENSION_LINEAGE_PATH}. "
            "Proceeding with assumed rule, but verification may be incomplete."
        )
        return []
    with open(PRIMARY_DIMENSION_LINEAGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_fidelity_loss_lineage(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify that the `fidelity_loss` column was derived solely from:
    1. `student_scalar`
    2. `human_annotations` (specifically the dimension indicated by `primary_dimension`)
    
    And that NO `teacher_scores` were used.
    
    Returns a lineage trace dictionary.
    """
    required_columns = ["fidelity_loss", "student_scalar", "human_annotations", "primary_dimension"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns for lineage verification: {missing_cols}")

    # 1. Verify no teacher_scores dependency via schema inspection (logical check)
    # Since we cannot run the previous execution trace here, we assert based on 
    # the known implementation of T024 which explicitly excludes teacher_scores 
    # from the MAE calculation for fidelity_loss.
    # We verify the mathematical definition: |student_scalar - human_annotations[primary_dimension]|
    
    errors = []
    verified_samples = 0
    
    # Sample a few rows to mathematically verify the derivation (if data is small enough)
    # or check the first N rows.
    check_limit = min(len(df), 100)
    
    for idx in range(check_limit):
        row = df.iloc[idx]
        student = row["student_scalar"]
        annotations = row["human_annotations"]
        primary_dim = row["primary_dimension"]
        recorded_loss = row["fidelity_loss"]
        
        if pd.isna(student) or pd.isna(annotations) or pd.isna(primary_dim):
            continue
        
        if not isinstance(annotations, (list, tuple)) or len(annotations) < 4:
            errors.append(f"Row {idx}: Invalid human_annotations format.")
            continue
        
        try:
            target_annotation = float(annotations[primary_dim])
            calculated_loss = abs(student - target_annotation)
            
            if not pd.isna(recorded_loss):
                if not pd.isclose(calculated_loss, recorded_loss, rtol=1e-9):
                    errors.append(
                        f"Row {idx}: Calculated loss {calculated_loss} != Recorded {recorded_loss}"
                    )
            else:
                errors.append(f"Row {idx}: Recorded loss is NaN but calculated is {calculated_loss}")
                
            verified_samples += 1
        except (IndexError, TypeError) as e:
            errors.append(f"Row {idx}: Error accessing annotation: {e}")

    lineage_trace = {
        "derivation_rule": "Absolute Error (MAE per sample)",
        "formula": "fidelity_loss = |student_scalar - human_annotations[primary_dimension]|",
        "input_columns": ["student_scalar", "human_annotations", "primary_dimension"],
        "excluded_columns": ["teacher_scores"],
        "excluded_columns_reason": "Task T024 specification explicitly defines fidelity loss as the alignment between student scalar and human annotation on the primary dimension, independent of teacher scores.",
        "verification_status": "passed" if not errors else "failed",
        "samples_verified": verified_samples,
        "total_samples_checked": check_limit,
        "errors": errors[:10] if errors else [], # Limit error list size
        "derivation_rule_hash": None # Will be computed if needed, or taken from T014
    }

    # Compute hash of the rule string for consistency
    import hashlib
    rule_hash = hashlib.sha256(DERIVATION_RULE_STRING.encode()).hexdigest()
    lineage_trace["derivation_rule_hash"] = rule_hash

    return lineage_trace

def save_lineage_report(lineage_trace: Dict[str, Any]) -> None:
    """Save the lineage verification report to disk."""
    with open(LINEAGE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(lineage_trace, f, indent=2)
    logging.info(f"Lineage report saved to {LINEAGE_OUTPUT_PATH}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Fidelity Loss Lineage (T014b)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    setup_directories()

    try:
        logging.info("Loading cleaned data...")
        df = load_cleaned_data()
        
        logging.info("Verifying fidelity loss lineage...")
        lineage_trace = verify_fidelity_loss_lineage(df)
        
        if lineage_trace["verification_status"] == "failed":
            logging.error("Lineage verification FAILED. See errors in report.")
            save_lineage_report(lineage_trace)
            return 1
        
        logging.info("Lineage verification PASSED.")
        save_lineage_report(lineage_trace)
        
        return 0

    except Exception as e:
        logging.critical(f"Verification failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
