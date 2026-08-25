"""
Provenance Validator for Perovskite Thermal Conductivity Data.

This module verifies that each entry in the merged dataset has a valid
peer-reviewed or NIST source reference, as required by FR-010.
"""

import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

# Import from sibling modules as per API surface
from utils.validation import setup_logger, handle_error

# Constants for valid source types
VALID_SOURCE_TYPES = {'peer-reviewed', 'nist', 'journal', 'refereed'}
REQUIRED_COLUMNS = ['source_reference', 'structure_id', 'thermal_conductivity']

def is_valid_source_reference(reference: Optional[str]) -> bool:
    """
    Check if a source reference string indicates a peer-reviewed or NIST source.

    Args:
        reference: The source reference string to validate.

    Returns:
        True if the reference is valid, False otherwise.
    """
    if reference is None or pd.isna(reference):
        return False

    ref_lower = str(reference).lower().strip()

    # Check for NIST references
    if 'nist' in ref_lower:
        return True

    # Check for journal/article indicators
    journal_indicators = [
        'doi:', 'journal', 'pubmed', 'sciencedirect', 'springer', 
        'elsevier', 'wiley', 'acs', 'royal society', 'nature', 
        'science', 'physical review', 'journal of', 'applied physics',
        'advanced materials', 'chemistry of materials'
    ]

    for indicator in journal_indicators:
        if indicator in ref_lower:
            return True

    # Check for DOI format (simplified check)
    if 'doi.org' in ref_lower or '10.' in ref_lower:
        return True

    return False

def validate_provenance(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate the provenance of all entries in the dataframe.

    Args:
        df: The merged dataframe with source_reference column.
        logger: Optional logger instance.

    Returns:
        Tuple of (validated dataframe, validation report dictionary)
    """
    if logger is None:
        logger = setup_logger('provenance_validator', logging.INFO)

    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        error_msg = f"Missing required columns: {missing}"
        handle_error(error_msg, level='critical')
        raise ValueError(error_msg)

    # Validate each row's source reference
    validation_results = []
    valid_count = 0
    invalid_count = 0

    for idx, row in df.iterrows():
        is_valid = is_valid_source_reference(row['source_reference'])
        validation_results.append({
            'index': idx,
            'structure_id': row['structure_id'],
            'source_reference': row['source_reference'],
            'is_valid': is_valid,
            'thermal_conductivity': row['thermal_conductivity']
        })

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            logger.warning(f"Invalid source reference at index {idx}: {row['source_reference']}")

    # Create validation report
    report = {
        'total_entries': len(df),
        'valid_entries': valid_count,
        'invalid_entries': invalid_count,
        'validity_rate': valid_count / len(df) if len(df) > 0 else 0.0,
        'validation_timestamp': pd.Timestamp.now().isoformat(),
        'validation_details': validation_results
    }

    # Filter to only valid entries
    valid_df = df[df.apply(lambda row: is_valid_source_reference(row['source_reference']), axis=1)].copy()

    logger.info(f"Provenance validation complete: {valid_count}/{len(df)} entries valid ({report['validity_rate']:.2%})")

    return valid_df, report

def filter_valid_provenance(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Filter the dataframe to keep only entries with valid provenance.

    Args:
        df: The merged dataframe.
        logger: Optional logger instance.

    Returns:
        Filtered dataframe with only valid provenance entries.
    """
    if logger is None:
        logger = setup_logger('provenance_validator', logging.INFO)

    valid_df, _ = validate_provenance(df, logger)

    if len(valid_df) < 50:
        error_msg = f"Insufficient samples after provenance filtering: {len(valid_df)} < 50"
        handle_error(error_msg, level='critical')
        raise ValueError(error_msg)

    return valid_df

def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.

    Args:
        report: The validation report dictionary.
        output_path: Path to save the JSON report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a summary version for the file (exclude full details if too large)
    summary_report = {
        'total_entries': report['total_entries'],
        'valid_entries': report['valid_entries'],
        'invalid_entries': report['invalid_entries'],
        'validity_rate': report['validity_rate'],
        'validation_timestamp': report['validation_timestamp'],
        'validation_details_count': len(report['validation_details']),
        'sample_invalid_entries': [
            detail for detail in report['validation_details'] 
            if not detail['is_valid']
        ][:10]  # Include first 10 invalid entries as sample
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, default=str)

    logging.info(f"Validation report saved to {output_path}")

def main() -> None:
    """
    Main entry point for the provenance validator script.
    
    Reads the cleaned merged data, validates provenance, filters valid entries,
    and saves the validation report.
    """
    logger = setup_logger('provenance_validator', logging.INFO)
    logger.info("Starting provenance validation...")

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / 'data' / 'cleaned' / 'merged_perovskite.csv'
    output_path = project_root / 'data' / 'cleaned' / 'merged_perovskite_provenance_validated.csv'
    report_path = project_root / 'data' / 'results' / 'provenance_validation_report.json'

    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        handle_error(error_msg, level='critical')
        raise FileNotFoundError(error_msg)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} entries")

    # Validate and filter
    valid_df, report = validate_provenance(df, logger)

    # Save validated data
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(valid_df)} valid entries to {output_path}")

    # Save validation report
    save_validation_report(report, report_path)
    logger.info(f"Saved validation report to {report_path}")

    logger.info("Provenance validation completed successfully")

if __name__ == '__main__':
    main()
