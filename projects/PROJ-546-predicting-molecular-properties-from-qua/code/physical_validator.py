"""
Physical Validator Module for Molecular Property Prediction Pipeline.

This module enforces structural constraints defined in the project specification,
specifically checking the physical validity of HOMO/LUMO energy relationships
in optimized geometries.

Constraint: HOMO_energy < LUMO_energy must hold for valid optimized geometries.
Violations are logged to logs/structural_failures.log with status 'failed_after_retry'
and the record is skipped from further processing.
"""

import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
LOGGER_NAME = "physical_validator"
LOG_FILE = "logs/structural_failures.log"

def setup_logger(log_file: str = None) -> logging.Logger:
    """
    Set up the logger for structural failures.

    Args:
        log_file: Path to the log file. Defaults to logs/structural_failures.log.

    Returns:
        Configured logger instance.
    """
    if log_file is None:
        # Resolve relative to project root (assuming code/ directory context)
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "structural_failures.log")

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler for structural failures
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Format: timestamp, level, message
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

def validate_homo_lumo_relationship(homo_energy: float, lumo_energy: float) -> Tuple[bool, str]:
    """
    Validate that HOMO energy is strictly less than LUMO energy.

    This is a fundamental physical constraint for stable molecular systems.
    In valid electronic structures, the Highest Occupied Molecular Orbital (HOMO)
    must have lower energy than the Lowest Unoccupied Molecular Orbital (LUMO).

    Args:
        homo_energy: HOMO energy value in eV.
        lumo_energy: LUMO energy value in eV.

    Returns:
        Tuple of (is_valid, status_message).
        - is_valid: True if HOMO < LUMO, False otherwise.
        - status_message: Description of the validation result.
    """
    if homo_energy >= lumo_energy:
        return False, f"FAILED: HOMO ({homo_energy:.6f} eV) >= LUMO ({lumo_energy:.6f} eV)"
    return True, f"PASSED: HOMO ({homo_energy:.6f} eV) < LUMO ({lumo_energy:.6f} eV)"

def log_structural_failure(
    logger: logging.Logger,
    molecule_id: str,
    homo_energy: float,
    lumo_energy: float,
    source_file: str = None,
    row_index: int = None
) -> None:
    """
    Log a structural failure to the structural_failures.log file.

    Args:
        logger: Logger instance to use.
        molecule_id: Identifier of the molecule that failed validation.
        homo_energy: HOMO energy value.
        lumo_energy: LUMO energy value.
        source_file: Source file where the data was read from (optional).
        row_index: Row index in the source file (optional).
    """
    location_info = ""
    if source_file:
        location_info += f"Source: {source_file}"
    if row_index is not None:
        location_info += f" Row: {row_index}"

    message = (
        f"[failed_after_retry] Molecule: {molecule_id} | "
        f"HOMO: {homo_energy:.6f} eV, LUMO: {lumo_energy:.6f} eV | "
        f"Violation: HOMO >= LUMO | Status: skipped"
    )
    if location_info:
        message += f" | {location_info}"

    logger.info(message)

def validate_descriptors_file(
    input_file: str,
    output_file: str = None,
    homo_column: str = "HOMO_energy",
    lumo_column: str = "LUMO_energy",
    id_column: str = "molecule_id"
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validate a descriptors CSV file for HOMO-LUMO energy relationships.

    Reads the input file, validates each row's HOMO/LUMO relationship,
    logs failures, and optionally writes a filtered output file.

    Args:
        input_file: Path to the input CSV file.
        output_file: Path to the output CSV file (filtered). If None, no output is written.
        homo_column: Name of the HOMO energy column.
        lumo_column: Name of the LUMO energy column.
        id_column: Name of the molecule identifier column.

    Returns:
        Tuple of (total_rows, valid_rows, failed_records).
        - total_rows: Total number of data rows processed.
        - valid_rows: Number of rows that passed validation.
        - failed_records: List of dictionaries containing failed record details.
    """
    logger = setup_logger()
    valid_records = []
    failed_records = []
    total_rows = 0
    valid_rows = 0

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Validate required columns exist
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV file has no headers")

        required_cols = {homo_column, lumo_column, id_column}
        missing_cols = required_cols - set(fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        for row_index, row in enumerate(reader, start=1):
            total_rows += 1
            molecule_id = row.get(id_column, f"unknown_row_{row_index}")

            try:
                homo_energy = float(row[homo_column])
                lumo_energy = float(row[lumo_column])
            except (ValueError, TypeError) as e:
                # Handle non-numeric values
                message = (
                    f"[failed_after_retry] Molecule: {molecule_id} | "
                    f"Error: Non-numeric energy values ({e}) | Status: skipped"
                )
                logger.info(message)
                failed_records.append({
                    "molecule_id": molecule_id,
                    "row_index": row_index,
                    "homo_energy": row.get(homo_column),
                    "lumo_energy": row.get(lumo_column),
                    "reason": f"Non-numeric values: {e}"
                })
                continue

            is_valid, status_msg = validate_homo_lumo_relationship(homo_energy, lumo_energy)

            if is_valid:
                valid_rows += 1
                valid_records.append(row)
            else:
                log_structural_failure(
                    logger,
                    molecule_id,
                    homo_energy,
                    lumo_energy,
                    source_file=input_file,
                    row_index=row_index
                )
                failed_records.append({
                    "molecule_id": molecule_id,
                    "row_index": row_index,
                    "homo_energy": homo_energy,
                    "lumo_energy": lumo_energy,
                    "reason": "HOMO >= LUMO"
                })

    # Write filtered output if requested
    if output_file and valid_records:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_records)

    return total_rows, valid_rows, failed_records

def main():
    """
    Main entry point for the physical validator script.

    Usage:
        python code/physical_validator.py --input data/descriptors_semi.csv --output data/descriptors_validated.csv

    This script:
    1. Reads the input descriptors CSV file.
    2. Validates each row's HOMO < LUMO constraint.
    3. Logs violations to logs/structural_failures.log.
    4. Writes a filtered CSV with only valid records (if output specified).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate HOMO-LUMO energy relationships in molecular descriptors."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input CSV file with molecular descriptors."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to output CSV file (filtered). If not specified, only validation is performed."
    )
    parser.add_argument(
        "--homo-col",
        default="HOMO_energy",
        help="Name of the HOMO energy column (default: HOMO_energy)"
    )
    parser.add_argument(
        "--lumo-col",
        default="LUMO_energy",
        help="Name of the LUMO energy column (default: LUMO_energy)"
    )
    parser.add_argument(
        "--id-col",
        default="molecule_id",
        help="Name of the molecule ID column (default: molecule_id)"
    )

    args = parser.parse_args()

    try:
        total, valid, failed = validate_descriptors_file(
            input_file=args.input,
            output_file=args.output,
            homo_column=args.homo_col,
            lumo_column=args.lumo_col,
            id_column=args.id_col
        )

        print(f"Validation complete:")
        print(f"  Total rows processed: {total}")
        print(f"  Valid rows: {valid}")
        print(f"  Failed rows: {len(failed)}")

        if failed:
            print(f"\nFailed records logged to: logs/structural_failures.log")
            for record in failed[:5]:  # Show first 5 failures
                print(f"  - {record['molecule_id']}: {record['reason']}")
            if len(failed) > 5:
                print(f"  ... and {len(failed) - 5} more")
        else:
            print("\nAll records passed validation.")

        if args.output:
            print(f"\nValidated data written to: {args.output}")

        # Exit with non-zero code if there were failures
        sys.exit(0 if not failed else 0)  # Note: We don't fail the pipeline on structural violations, just skip them

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
