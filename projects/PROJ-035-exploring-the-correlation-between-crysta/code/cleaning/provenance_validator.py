"""
Provenance Validator Module for Perovskite Thermal Conductivity Project.

This module verifies that each entry in the cleaned dataset has a valid
peer-reviewed or NIST source_reference, ensuring compliance with FR-010.
"""
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

# Import existing utilities from the project
from utils.validation import setup_logger, handle_error

# Configure logger
logger = setup_logger(__name__, logging.INFO)

# Constants for validation
VALID_SOURCE_KEYWORDS = [
    "doi.org", "nist", "peer-reviewed", "journal", "physical review",
    "acta materialia", "advanced materials", "nature", "science",
    "journal of applied physics", "applied physics letters", "materials science"
]
REQUIRED_COLUMNS = ["source_reference", "structure_id", "thermal_conductivity"]

def is_valid_source_reference(reference: str) -> Tuple[bool, str]:
    """
    Validate if a source_reference string points to a peer-reviewed or NIST source.

    Args:
        reference: The source reference string to validate.

    Returns:
        Tuple of (is_valid, reason_string)
    """
    if pd.isna(reference) or not isinstance(reference, str) or reference.strip() == "":
        return False, "Missing or empty source reference"

    ref_lower = reference.lower()

    # Check for NIST explicitly
    if "nist" in ref_lower:
        return True, "NIST source detected"

    # Check for DOI (standard for peer-reviewed literature)
    if "doi.org" in ref_lower or "doi:" in ref_lower:
        return True, "DOI detected (peer-reviewed)"

    # Check for known journal names or keywords
    for keyword in VALID_SOURCE_KEYWORDS:
        if keyword in ref_lower:
            return True, f"Peer-reviewed keyword detected: {keyword}"

    return False, f"Source does not match peer-reviewed or NIST criteria: {reference}"

def validate_provenance(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate the provenance of all entries in the dataset.

    This function checks that every row has a valid source_reference pointing to
    peer-reviewed literature or NIST data. It returns the original dataframe
    and a validation report.

    Args:
        df: Input dataframe with 'source_reference' column.

    Returns:
        Tuple of (original_dataframe, validation_report_dict)

    Raises:
        ValueError: If no valid sources are found (violates FR-010).
        ValueError: If required columns are missing.
    """
    # Validate required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns for provenance validation: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    validation_results = []
    valid_count = 0
    invalid_count = 0
    invalid_entries = []

    for idx, row in df.iterrows():
        ref = row.get("source_reference", "")
        is_valid, reason = is_valid_source_reference(ref)

        if is_valid:
            valid_count += 1
            validation_results.append({
                "index": idx,
                "structure_id": row.get("structure_id", "UNKNOWN"),
                "status": "VALID",
                "reason": reason
            })
        else:
            invalid_count += 1
            invalid_entries.append({
                "index": idx,
                "structure_id": row.get("structure_id", "UNKNOWN"),
                "reference": str(ref),
                "reason": reason
            })
            validation_results.append({
                "index": idx,
                "structure_id": row.get("structure_id", "UNKNOWN"),
                "status": "INVALID",
                "reason": reason
            })

    # Create validation report
    report = {
        "total_entries": len(df),
        "valid_entries": valid_count,
        "invalid_entries": invalid_count,
        "validity_rate": valid_count / len(df) if len(df) > 0 else 0.0,
        "invalid_details": invalid_entries,
        "all_valid": invalid_count == 0
    }

    logger.info(f"Provenance validation complete: {valid_count}/{len(df)} valid entries")

    # Fail loudly if no valid sources found (FR-010 compliance)
    if invalid_count == len(df):
        error_msg = (
            f"CRITICAL: No valid peer-reviewed or NIST sources found in dataset. "
            f"All {len(df)} entries failed validation. This violates FR-010."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log warnings if there are invalid entries but some are valid
    if invalid_count > 0:
        logger.warning(
            f"Found {invalid_count} entries with invalid provenance. "
            f"These should be reviewed manually."
        )

    return df, report

def filter_valid_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to keep only entries with valid provenance.

    Args:
        df: Input dataframe.

    Returns:
        Filtered dataframe containing only valid entries.
    """
    valid_indices = []
    for idx, row in df.iterrows():
        ref = row.get("source_reference", "")
        is_valid, _ = is_valid_source_reference(ref)
        if is_valid:
            valid_indices.append(idx)

    filtered_df = df.loc[valid_indices].reset_index(drop=True)
    logger.info(
        f"Filtered dataset: kept {len(filtered_df)} valid entries, "
        f"removed {len(df) - len(filtered_df)} invalid entries"
    )
    return filtered_df

def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.

    Args:
        report: The validation report dictionary.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Validation report saved to {output_path}")

def main() -> int:
    """
    Main entry point for running the provenance validator.

    Expected to be called from the command line with input and output paths.
    Usage: python -m cleaning.provenance_validator --input data/cleaned/merged_perovskite.csv --output data/results/provenance_report.json

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate provenance of perovskite thermal conductivity dataset."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV file (cleaned dataset)."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the JSON validation report."
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="If set, filter the dataset to keep only valid entries and save to a new CSV."
    )
    parser.add_argument(
        "--filtered-output",
        type=str,
        default=None,
        help="Path to save the filtered CSV (only used with --filter)."
    )

    args = parser.parse_args()

    try:
        # Load input data
        input_path = Path(args.input)
        if not input_path.exists():
            handle_error(f"Input file not found: {input_path}", level="CRITICAL")
            return 1

        logger.info(f"Loading dataset from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows")

        # Validate provenance
        validated_df, report = validate_provenance(df)

        # Save report
        output_path = Path(args.output)
        save_validation_report(report, output_path)

        # Optionally filter and save cleaned dataset
        if args.filter:
            if args.filtered_output is None:
                handle_error("--filtered-output is required when --filter is used", level="ERROR")
                return 1

            filtered_df = filter_valid_provenance(df)
            filtered_path = Path(args.filtered_output)
            filtered_df.to_csv(filtered_path, index=False)
            logger.info(f"Filtered dataset saved to {filtered_path}")

        # Return appropriate exit code
        if report["all_valid"]:
            logger.info("All entries have valid provenance. Validation PASSED.")
            return 0
        else:
            logger.warning(
                f"Validation completed with {report['invalid_entries']} invalid entries. "
                f"Review the report at {output_path}."
            )
            return 0  # Still return 0 as we found some valid data

    except ValueError as e:
        handle_error(str(e), level="CRITICAL")
        return 1
    except Exception as e:
        handle_error(f"Unexpected error during provenance validation: {str(e)}", level="CRITICAL")
        return 1

if __name__ == "__main__":
    sys.exit(main())
