"""
Provenance Validator Module for Perovskite Thermal Conductivity Project.

This module verifies that all entries in the merged dataset have valid
peer-reviewed or NIST source references using regex patterns for:
- DOI: 10.\d{4}/.*/.
- PMID: 10.\d{4}/\d+
- NIST ID: NIST-[A-Z0-9]+

Outputs a validation report to data/cleaned/provenance_report.json
and exits with code 1 if any entry lacks valid provenance (FR-010).
"""

import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import from existing API surface
from utils.validation import setup_logger, handle_error


def setup_logger_module(name: str = "provenance_validator", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger for this module.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name, level)


def is_valid_source_reference(reference: str) -> bool:
    """
    Check if a source reference string matches valid provenance patterns.
    
    Valid patterns:
    - DOI: 10.\d{4}/.*/. (e.g., 10.1038/s41524-021-00567-8)
    - PMID: 10.\d{4}/\d+ (e.g., 10.1000/12345)
    - NIST ID: NIST-[A-Z0-9]+ (e.g., NIST-ABC123)
    
    Args:
        reference: Source reference string to validate
        
    Returns:
        True if reference matches any valid pattern, False otherwise
    """
    if not isinstance(reference, str) or not reference.strip():
        return False
    
    reference = reference.strip()
    
    # DOI pattern: 10.\d{4}/.*/.
    doi_pattern = r'^10\.\d{4}/.*/.*$'
    
    # PMID pattern: 10.\d{4}/\d+
    pmid_pattern = r'^10\.\d{4}/\d+$'
    
    # NIST ID pattern: NIST-[A-Z0-9]+
    nist_pattern = r'^NIST-[A-Z0-9]+$'
    
    if re.match(doi_pattern, reference):
        return True
    if re.match(pmid_pattern, reference):
        return True
    if re.match(nist_pattern, reference):
        return True
    
    return False


def validate_provenance(df: Any, column_name: str = "source_reference") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate provenance for all entries in a DataFrame.
    
    Args:
        df: DataFrame containing the source_reference column
        column_name: Name of the column to validate (default: "source_reference")
        
    Returns:
        Tuple of (valid_entries, invalid_entries) where each entry is a dict
        containing the row data and validation status.
    """
    valid_entries = []
    invalid_entries = []
    
    for idx, row in df.iterrows():
        reference = row.get(column_name, "")
        is_valid = is_valid_source_reference(reference)
        
        entry = {
            "row_index": int(idx),
            "structure_id": row.get("structure_id", "unknown"),
            "source_reference": reference,
            "is_valid": is_valid
        }
        
        if is_valid:
            valid_entries.append(entry)
        else:
            invalid_entries.append(entry)
    
    return valid_entries, invalid_entries


def filter_valid_provenance(df: Any, column_name: str = "source_reference") -> Any:
    """
    Filter DataFrame to keep only rows with valid provenance.
    
    Args:
        df: Input DataFrame
        column_name: Name of the source_reference column
        
    Returns:
        Filtered DataFrame containing only valid entries
    """
    valid_mask = df[column_name].apply(is_valid_source_reference)
    return df[valid_mask].reset_index(drop=True)


def save_validation_report(valid_count: int, invalid_count: int, 
                           valid_entries: List[Dict[str, Any]], 
                           invalid_entries: List[Dict[str, Any]],
                           output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    
    Args:
        valid_count: Number of valid entries
        invalid_count: Number of invalid entries
        valid_entries: List of valid entry details
        invalid_entries: List of invalid entry details
        output_path: Path to save the report
    """
    report = {
        "summary": {
            "total_entries": valid_count + invalid_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "validation_rate": valid_count / (valid_count + invalid_count) if (valid_count + invalid_count) > 0 else 0.0
        },
        "valid_entries": valid_entries,
        "invalid_entries": invalid_entries
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)


def main() -> int:
    """
    Main entry point for the provenance validator.
    
    Reads the merged perovskite dataset, validates provenance for each entry,
    saves the validation report, and exits with code 1 if any entry lacks
    valid provenance.
    
    Returns:
        Exit code: 0 if all entries have valid provenance, 1 otherwise
    """
    logger = setup_logger_module()
    logger.info("Starting provenance validation...")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "cleaned" / "merged_perovskite.csv"
    output_path = project_root / "data" / "cleaned" / "provenance_report.json"
    
    # Check if input file exists
    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return 1
    
    try:
        import pandas as pd
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} entries from {input_path}")
    except Exception as e:
        error_msg = f"Failed to read input file: {e}"
        logger.error(error_msg)
        handle_error(error_msg)
        return 1
    
    # Validate provenance
    valid_entries, invalid_entries = validate_provenance(df, "source_reference")
    valid_count = len(valid_entries)
    invalid_count = len(invalid_entries)
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    
    # Save report
    save_validation_report(valid_count, invalid_count, valid_entries, invalid_entries, output_path)
    logger.info(f"Validation report saved to {output_path}")
    
    # Exit with error code if any invalid entries found
    if invalid_count > 0:
        error_msg = f"Provenance validation failed: {invalid_count} entries lack valid provenance"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return 1
    
    logger.info("All entries have valid provenance. Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
