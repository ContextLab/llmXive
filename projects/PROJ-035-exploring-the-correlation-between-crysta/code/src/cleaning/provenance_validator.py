import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.validation import setup_logger, handle_error

PROVENANCE_REPORT_PATH = Path("data/cleaned/provenance_report.json")
MERGED_DATA_PATH = Path("data/cleaned/merged_perovskite.csv") # Input might be raw merged or thermal
# The task says: "verify peer-reviewed/NIST source_reference for each entry"
# We assume the input is the thermal data or the merged data.
# Let's assume we validate the thermal data before merge or the merged data.
# Given the pipeline: Fetch Thermal -> Validate Provenance -> Normalize -> Merge.
# So we validate the thermal data.
THERMAL_RAW_PATH = Path("data/raw/thermal_raw.csv")

def is_valid_source_reference(ref: Optional[str]) -> bool:
    """
    Check if the source reference matches DOI, PMID, or NIST ID patterns.
    """
    if not ref or pd.isna(ref):
        return False
    
    ref = str(ref).strip()
    
    # DOI pattern: 10.\d{4}/.*
    doi_pattern = r'^10\.\d{4,}/.*$'
    # PMID pattern: 10.\d{4}/\d+ (Note: PMID is usually just numbers, but task says 10.x pattern)
    # The task says: PMID (10.\d{4}/\d+). This looks like a DOI pattern for PMID.
    pmid_pattern = r'^10\.\d{4,}/\d+$' 
    # NIST ID pattern: ^NIST-[0-9]{4}-[A-Z0-9]{6,10}$
    nist_pattern = r'^NIST-\d{4}-[A-Z0-9]{6,10}$'
    
    if re.match(doi_pattern, ref):
        return True
    if re.match(nist_pattern, ref):
        return True
    # If the task implies PMID is different, we might need to adjust, but based on regex provided:
    # "PMID (10.\d{4}/\d+)" is a subset of DOI.
    
    return False

def validate_provenance(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Validate the 'source_reference' column in the dataframe.
    Returns (valid_indices, invalid_indices).
    """
    valid = []
    invalid = []
    
    if 'source_reference' not in df.columns:
        raise ValueError("DataFrame missing 'source_reference' column.")
    
    for idx, row in df.iterrows():
        ref = row['source_reference']
        if is_valid_source_reference(ref):
            valid.append(idx)
        else:
            invalid.append(idx)
    
    return valid, invalid

def filter_valid_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a dataframe containing only rows with valid provenance.
    """
    valid_indices, _ = validate_provenance(df)
    return df.loc[valid_indices].reset_index(drop=True)

def save_validation_report(valid_count: int, invalid_count: int, output_path: Path):
    """
    Save the validation report to JSON.
    """
    report = {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_count": valid_count + invalid_count,
        "timestamp": str(pd.Timestamp.now())
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """
    Main entry point for provenance validation.
    Reads from data/raw/thermal_raw.csv, validates, and saves report.
    If invalid entries exist, it logs them but does NOT fail the pipeline immediately
    unless the task requires strict halting. The task says: "Exit with code 1 if any entry lacks valid provenance."
    """
    logger = setup_logger("provenance_validator")
    
    if not THERMAL_RAW_PATH.exists():
        logger.error(f"Input file {THERMAL_RAW_PATH} not found.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(THERMAL_RAW_PATH)
    except Exception as e:
        logger.error(f"Failed to read {THERMAL_RAW_PATH}: {e}")
        sys.exit(1)
    
    valid_indices, invalid_indices = validate_provenance(df)
    
    logger.info(f"Valid: {len(valid_indices)}, Invalid: {len(invalid_indices)}")
    
    save_validation_report(len(valid_indices), len(invalid_indices), PROVENANCE_REPORT_PATH)
    
    if len(invalid_indices) > 0:
        logger.error("Found entries with invalid provenance.")
        # The task says: "Exit with code 1 if any entry lacks valid provenance."
        sys.exit(1)
    
    logger.info("Provenance validation passed.")

if __name__ == "__main__":
    main()
