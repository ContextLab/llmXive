import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd

from src.utils.validation import setup_logger, handle_error

# Regex patterns for valid provenance identifiers
# DOI: 10.xxxx/... (standard format)
DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s]+')
# PMID: 10.0000/00000000 format or standard numeric PMID (8 digits usually)
# The task specifies: PMID (10.\d{4}/\d+) which looks like a specific format or a typo for DOIs,
# but we will strictly follow the task regex: 10.\d{4}/\d+
PMID_PATTERN = re.compile(r'10\.\d{4}/\d+')
# NIST ID: NIST-[A-Z0-9]+
NIST_PATTERN = re.compile(r'NIST-[A-Z0-9]+')

def is_valid_source_reference(reference: Optional[str]) -> Tuple[bool, str]:
    """
    Verify if a source_reference string matches a valid DOI, PMID, or NIST ID pattern.
    
    Args:
        reference: The source reference string to validate.
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if pd.isna(reference) or not isinstance(reference, str) or reference.strip() == "":
        return False, "Reference is missing or empty"
    
    ref = reference.strip()
    
    if DOI_PATTERN.search(ref):
        return True, "Valid DOI detected"
    if PMID_PATTERN.search(ref):
        return True, "Valid PMID detected"
    if NIST_PATTERN.search(ref):
        return True, "Valid NIST ID detected"
        
    return False, "No valid DOI, PMID, or NIST ID pattern found"

def validate_provenance(df: pd.DataFrame, column_name: str = "source_reference") -> Dict[str, Any]:
    """
    Validate the provenance of all entries in the dataframe.
    
    Args:
        df: Input dataframe containing the source_reference column.
        column_name: Name of the column to validate.
        
    Returns:
        Dictionary containing validation results:
        - 'total_count': Total rows processed
        - 'valid_count': Number of valid references
        - 'invalid_count': Number of invalid references
        - 'failed_indices': List of indices with invalid references
        - 'failed_reasons': List of reasons for failure
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in dataframe")
    
    results = {
        "total_count": len(df),
        "valid_count": 0,
        "invalid_count": 0,
        "failed_indices": [],
        "failed_reasons": [],
        "details": []
    }
    
    for idx, row in df.iterrows():
        ref = row.get(column_name)
        is_valid, reason = is_valid_source_reference(ref)
        
        if is_valid:
            results["valid_count"] += 1
        else:
            results["invalid_count"] += 1
            results["failed_indices"].append(idx)
            results["failed_reasons"].append(reason)
            results["details"].append({
                "index": idx,
                "value": str(ref) if not pd.isna(ref) else "None",
                "reason": reason
            })
    
    return results

def filter_valid_provenance(df: pd.DataFrame, column_name: str = "source_reference") -> pd.DataFrame:
    """
    Filter the dataframe to keep only rows with valid provenance.
    
    Args:
        df: Input dataframe.
        column_name: Name of the column to validate.
        
    Returns:
        Filtered dataframe containing only valid rows.
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in dataframe")
        
    valid_mask = df[column_name].apply(lambda x: is_valid_source_reference(x)[0])
    return df[valid_mask].reset_index(drop=True)

def save_validation_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    
    Args:
        results: Dictionary containing validation results.
        output_path: Path to save the JSON report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def main():
    """
    CLI entry point for the provenance validator.
    Expects input CSV at data/cleaned/thermal_raw.csv (or similar) and outputs report to data/cleaned/provenance_report.json.
    Based on T014 task description, it should process the thermal data merged with structures.
    Since T015 (clean_merge) hasn't run yet in this isolated task context, we assume the input 
    is the raw thermal data fetched by T014b, which is expected to be at data/raw/thermal_raw.csv.
    However, the task says "verify peer-reviewed/NIST source_reference for each entry".
    The most logical place to run this is on the thermal data before merging, or on the merged data.
    Given T015 depends on T014, and T015 merges structures and thermal, T014 likely validates the thermal source.
    
    We will look for data/raw/thermal_raw.csv first (output of T014b).
    If not found, we check if a merged file exists, but primarily we target the thermal input.
    """
    logger = setup_logger("provenance_validator", logging.INFO)
    
    # Determine input path
    input_path = Path("data/raw/thermal_raw.csv")
    if not input_path.exists():
        # Fallback to potential merged location if raw is missing (for integration scenarios)
        input_path = Path("data/cleaned/merged_perovskite.csv")
        
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # Check if we are running in a context where data hasn't been generated yet.
        # For the purpose of this script execution in the pipeline, we must fail loudly if input is missing.
        sys.exit(1)
        
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)
        
    if "source_reference" not in df.columns:
        logger.error("Column 'source_reference' not found in input data.")
        sys.exit(1)
        
    logger.info(f"Validating provenance for {len(df)} entries...")
    results = validate_provenance(df, "source_reference")
    
    output_path = Path("data/cleaned/provenance_report.json")
    save_validation_report(results, output_path)
    
    logger.info(f"Validation complete. Valid: {results['valid_count']}, Invalid: {results['invalid_count']}")
    logger.info(f"Report saved to {output_path}")
    
    if results["invalid_count"] > 0:
        logger.error("Validation failed: Some entries lack valid provenance.")
        sys.exit(1)
    else:
        logger.info("All entries have valid provenance.")
        sys.exit(0)

if __name__ == "__main__":
    main()
