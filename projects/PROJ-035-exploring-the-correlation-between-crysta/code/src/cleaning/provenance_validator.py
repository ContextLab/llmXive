"""
Provenance validator for thermal conductivity data.

This module validates that each entry in the thermal conductivity dataset
has a valid peer-reviewed or NIST source reference (DOI, PMID, or NIST ID).

Usage:
    python src/cleaning/provenance_validator.py --input data/raw/thermal_raw.csv --output data/cleaned/provenance_report.json
"""
import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Import seed management
from src.utils.seed_manager import init_seed, add_seed_argument, get_seed, is_seed_initialized
from src.utils.validation import setup_logger, handle_error

# Regex patterns for validation
DOI_PATTERN = re.compile(r'10\.\d{4}/.*/.')
PMID_PATTERN = re.compile(r'10\.\d{4}/\d+')
NIST_PATTERN = re.compile(r'NIST-[A-Z0-9]+')


def is_valid_source_reference(reference: str) -> bool:
    """
    Check if a source reference is valid (DOI, PMID, or NIST ID).
    
    Args:
        reference: The source reference string.
    
    Returns:
        True if the reference is valid, False otherwise.
    """
    if pd.isna(reference) or not isinstance(reference, str):
        return False
    
    reference = reference.strip()
    if not reference:
        return False
    
    # Check for DOI
    if DOI_PATTERN.search(reference):
        return True
    
    # Check for PMID
    if PMID_PATTERN.search(reference):
        return True
    
    # Check for NIST ID
    if NIST_PATTERN.search(reference):
        return True
    
    return False


def validate_provenance(df: pd.DataFrame, source_column: str = "source_reference") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate provenance for all entries in the dataframe.
    
    Args:
        df: Input dataframe.
        source_column: Name of the column containing source references.
    
    Returns:
        Tuple of (filtered dataframe with valid provenance, validation report).
    """
    logger = setup_logger(__name__)
    
    if source_column not in df.columns:
        raise ValueError(f"Column '{source_column}' not found in dataframe")
    
    valid_mask = df[source_column].apply(is_valid_source_reference)
    
    valid_count = valid_mask.sum()
    invalid_count = len(df) - valid_count
    
    report = {
        "total_entries": len(df),
        "valid_entries": int(valid_count),
        "invalid_entries": int(invalid_count),
        "validity_rate": float(valid_count / len(df)) if len(df) > 0 else 0.0
    }
    
    logger.info(f"Validation complete: {valid_count}/{len(df)} entries have valid provenance")
    
    return df[valid_mask].copy(), report


def filter_valid_provenance(df: pd.DataFrame, source_column: str = "source_reference") -> pd.DataFrame:
    """
    Filter dataframe to keep only entries with valid provenance.
    
    Args:
        df: Input dataframe.
        source_column: Name of the column containing source references.
    
    Returns:
        Filtered dataframe.
    """
    valid_df, _ = validate_provenance(df, source_column)
    return valid_df


def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    
    Args:
        report: The validation report dictionary.
        output_path: Path to save the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate provenance of thermal conductivity data")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/cleaned/provenance_report.json", help="Output report file path")
    parser.add_argument("--source-column", type=str, default="source_reference", help="Column name for source references")
    parser = add_seed_argument(parser)
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger = setup_logger(__name__)
        logger.info(f"Loading data from {input_path}")
        
        df = pd.read_csv(input_path)
        
        logger.info(f"Validating provenance for {len(df)} entries")
        
        valid_df, report = validate_provenance(df, args.source_column)
        
        # Exit with code 1 if any entry lacks valid provenance
        if report["invalid_entries"] > 0:
            logger.error(f"Found {report['invalid_entries']} entries with invalid provenance. Exiting.")
            save_validation_report(report, output_path)
            sys.exit(1)
        
        # Save report
        save_validation_report(report, output_path)
        logger.info(f"Validation report saved to {output_path}")
        
        # Optionally save the filtered dataframe
        filtered_output = output_path.parent / "thermal_validated.csv"
        valid_df.to_csv(filtered_output, index=False)
        logger.info(f"Validated data saved to {filtered_output}")
        
    except Exception as e:
        handle_error(f"Error in provenance_validator: {e}", level="CRITICAL")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    main()
