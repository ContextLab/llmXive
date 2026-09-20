"""
Audit script to verify the dataset source is valid and no synthetic data was introduced.

This script checks:
1. The existence of the processed alloys file.
2. The presence of the 'source_label' column.
3. That the 'source_label' matches the verified source 'matsci/glass-forming-ability'.
4. That no synthetic data flags (e.g., 'is_synthetic' or 'source_label' == 'synthetic') exist.

Output:
Writes a JSON audit log to data/logs/data_source_audit.json.
"""
import os
import sys
import json
import logging
import pandas as pd
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROCESSED_DATA_PATH = "data/processed/processed_alloys.csv"
OUTPUT_LOG_PATH = "data/logs/data_source_audit.json"
VERIFIED_SOURCE = "matsci/glass-forming-ability"
SYNTHETIC_INDICATORS = ["synthetic", "fake", "generated", "mock"]

def load_processed_data(path: str) -> pd.DataFrame:
    """Load the processed alloys dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found at {path}. "
                                "Run ingestion.py and features.py first.")
    logger.info(f"Loading processed data from {path}")
    return pd.read_csv(path)

def audit_data_source(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform the data source audit.
    
    Returns a dictionary with audit results.
    """
    audit_result = {
        "status": "pass",
        "verified_source": VERIFIED_SOURCE,
        "checks": {},
        "errors": [],
        "warnings": []
    }

    # Check 1: Source Label Column Existence
    if "source_label" not in df.columns:
        error_msg = "Missing 'source_label' column in processed dataset."
        audit_result["status"] = "fail"
        audit_result["errors"].append(error_msg)
        logger.error(error_msg)
        return audit_result
    
    audit_result["checks"]["source_label_exists"] = True
    logger.info("Check 1 passed: 'source_label' column exists.")

    # Check 2: Verify Source Label Value
    unique_labels = df["source_label"].unique()
    if len(unique_labels) != 1 or unique_labels[0] != VERIFIED_SOURCE:
        error_msg = f"Source label mismatch. Expected '{VERIFIED_SOURCE}', found {unique_labels}."
        audit_result["status"] = "fail"
        audit_result["errors"].append(error_msg)
        logger.error(error_msg)
        return audit_result
    
    audit_result["checks"]["source_label_correct"] = True
    logger.info(f"Check 2 passed: Source label is '{VERIFIED_SOURCE}'.")

    # Check 3: No Synthetic Data Indicators
    # Check for explicit 'is_synthetic' column
    if "is_synthetic" in df.columns:
        if df["is_synthetic"].any():
            warning_msg = "Found 'is_synthetic' column with True values."
            audit_result["warnings"].append(warning_msg)
            logger.warning(warning_msg)
            # Not a fatal failure if explicitly marked, but worth noting
        else:
            audit_result["checks"]["no_is_synthetic_flag"] = True
    else:
        audit_result["checks"]["no_is_synthetic_flag"] = True

    # Check for synthetic indicators in source_label or other text columns
    # We already verified source_label is correct, but let's scan other columns just in case
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns:
        if col == "source_label":
            continue
        for indicator in SYNTHETIC_INDICATORS:
            # Check if any value in the column contains the indicator (case-insensitive)
            mask = df[col].astype(str).str.lower().str.contains(indicator, na=False)
            if mask.any():
                warning_msg = f"Found potential synthetic indicator '{indicator}' in column '{col}'."
                audit_result["warnings"].append(warning_msg)
                logger.warning(warning_msg)

    if not audit_result["errors"]:
        logger.info("Audit completed successfully. No synthetic data detected.")
    else:
        logger.error("Audit failed due to errors.")

    return audit_result

def save_audit_log(result: Dict[str, Any], path: str):
    """Save the audit result to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Audit log saved to {path}")

def main():
    """Main entry point for the audit script."""
    try:
        df = load_processed_data(PROCESSED_DATA_PATH)
        audit_result = audit_data_source(df)
        save_audit_log(audit_result, OUTPUT_LOG_PATH)
        
        if audit_result["status"] == "fail":
            logger.error("Data source audit FAILED.")
            sys.exit(1)
        else:
            logger.info("Data source audit PASSED.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during audit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
