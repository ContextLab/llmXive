"""
Provenance Validator Module for Perovskite Thermal Conductivity Pipeline.

This module verifies that every entry in the thermal conductivity dataset
has a valid peer-reviewed or NIST source reference. It validates against
three patterns:
1. DOI: 10.\\d{4}/.*
2. PMID: 10.\\d{4}/\\d+ (Note: Standard PMID is usually 7-10 digits, but per
   task spec T014, we strictly follow the regex provided: 10.\\d{4}/\\d+)
3. NIST ID: NIST-[A-Z0-9]+

It outputs a JSON report to data/cleaned/provenance_report.json and exits
with code 1 if any entry lacks valid provenance.
"""
import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

# Import base validation utilities from T007/T009
from src.utils.validation import setup_logger, handle_error


# Regular expressions for validation
# DOI pattern: 10.XXXX/...
DOI_PATTERN = re.compile(r'^10\.\d{4}/.*', re.IGNORECASE)
# PMID pattern as specified in task: 10.XXXX/XXXX (Note: This looks like a specific format or a typo in the prompt, 
# but we must follow the prompt's regex strictly: 10.\\d{4}/\\d+)
PMID_PATTERN = re.compile(r'^10\.\d{4}/\d+$')
# NIST ID pattern: NIST-[A-Z0-9]+
NIST_PATTERN = re.compile(r'^NIST-[A-Z0-9]+$', re.IGNORECASE)

# Combined pattern for efficiency
VALIDATION_PATTERNS = [DOI_PATTERN, PMID_PATTERN, NIST_PATTERN]


def is_valid_source_reference(reference: Optional[str]) -> bool:
    """
    Check if a source reference string matches any of the valid patterns.

    Args:
        reference: The source reference string to validate (e.g., DOI, PMID, NIST ID).

    Returns:
        bool: True if the reference matches a valid pattern, False otherwise.
    """
    if not isinstance(reference, str) or not reference.strip():
        return False

    ref_clean = reference.strip()

    for pattern in VALIDATION_PATTERNS:
        if pattern.match(ref_clean):
            return True

    return False


def validate_provenance(df: pd.DataFrame, column_name: str = 'source_reference') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate the 'source_reference' column for all rows in the dataframe.

    Args:
        df: Input pandas DataFrame containing the data.
        column_name: Name of the column containing source references.

    Returns:
        Tuple containing:
            - DataFrame with an added 'provenance_valid' boolean column.
            - Dictionary with validation statistics (total, passed, failed).
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in dataframe. Available columns: {list(df.columns)}")

    # Apply validation
    df = df.copy()
    df['provenance_valid'] = df[column_name].apply(is_valid_source_reference)

    passed_count = df['provenance_valid'].sum()
    failed_count = len(df) - passed_count

    stats = {
        'total_records': len(df),
        'passed': int(passed_count),
        'failed': int(failed_count),
        'pass_rate': passed_count / len(df) if len(df) > 0 else 0.0
    }

    return df, stats


def filter_valid_provenance(df: pd.DataFrame, column_name: str = 'source_reference') -> pd.DataFrame:
    """
    Filter the dataframe to keep only rows with valid provenance.

    Args:
        df: Input pandas DataFrame.
        column_name: Name of the column containing source references.

    Returns:
        Filtered DataFrame containing only valid entries.
    """
    df_validated, _ = validate_provenance(df, column_name)
    return df_validated[df_validated['provenance_valid']].copy()


def save_validation_report(stats: Dict[str, Any], output_path: Path, failed_entries: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Save the validation report to a JSON file.

    Args:
        stats: Dictionary containing validation statistics.
        output_path: Path to the output JSON file.
        failed_entries: Optional list of dictionaries containing details of failed entries.
    """
    report = {
        'validation_stats': stats,
        'timestamp': pd.Timestamp.now().isoformat(),
        'tool': 'provenance_validator'
    }
    if failed_entries:
        report['failed_entries'] = failed_entries

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)


def main() -> int:
    """
    Main entry point for the provenance validator CLI.

    Expects input data at data/cleaned/thermal_raw.csv (or specified via args)
    and outputs report to data/cleaned/provenance_report.json.
    """
    logger = setup_logger('provenance_validator', logging.INFO)
    logger.info("Starting Provenance Validation...")

    # Default paths
    input_path = Path("data/cleaned/thermal_raw.csv")
    output_report_path = Path("data/cleaned/provenance_report.json")

    # Check if input file exists
    if not input_path.exists():
        # Fallback to raw data if cleaned doesn't exist yet, as per pipeline flow
        # T014b outputs to data/raw/thermal_raw.csv, T014 runs after T014b.
        # However, T014 description says "verify... for each entry".
        # Let's check data/raw/thermal_raw.csv if data/cleaned/ is missing.
        raw_input = Path("data/raw/thermal_raw.csv")
        if raw_input.exists():
            input_path = raw_input
            logger.info(f"Input file not found at {input_path}, using {raw_input}")
        else:
            logger.error(f"Input file not found at {input_path} or {raw_input}")
            return 1

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return 1

    if 'source_reference' not in df.columns:
        logger.error(f"Column 'source_reference' not found in {input_path}")
        return 1

    # Validate
    df_validated, stats = validate_provenance(df, 'source_reference')

    # Collect failed entries for the report
    failed_entries = []
    if stats['failed'] > 0:
        failed_df = df_validated[~df_validated['provenance_valid']]
        for idx, row in failed_df.iterrows():
            failed_entries.append({
                'index': int(idx),
                'structure_id': row.get('structure_id', 'N/A'),
                'source_reference': str(row['source_reference']),
                'reason': 'Invalid format (Expected DOI, PMID, or NIST ID)'
            })

    # Save report
    save_validation_report(stats, output_report_path, failed_entries)
    logger.info(f"Validation report saved to {output_report_path}")
    logger.info(f"Passed: {stats['passed']}, Failed: {stats['failed']}, Pass Rate: {stats['pass_rate']:.2%}")

    # Exit with code 1 if any entry lacks valid provenance
    if stats['failed'] > 0:
        logger.error("Validation failed: One or more entries lack valid provenance.")
        return 1

    logger.info("Provenance validation successful.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
