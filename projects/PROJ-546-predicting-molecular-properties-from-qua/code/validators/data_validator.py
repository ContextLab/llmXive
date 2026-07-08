"""
Data validation module for the molecular properties dataset.

Verifies downloaded CSV files contain required columns and correct data types
as per FR-001.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["SMILES", "experimental_barrier"]
SMILES_COLUMN = "SMILES"
BARRIER_COLUMN = "experimental_barrier"

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_csv_structure(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates that the CSV file exists and contains the required columns.

    Args:
        file_path: Path to the CSV file to validate.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header is None:
                errors.append("CSV file is empty or has no header row.")
                return False, errors

            # Check for required columns
            header_set = set(col.strip() for col in header)
            missing_cols = set(REQUIRED_COLUMNS) - header_set

            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return False, errors

            logger.info(f"CSV structure validated. Found columns: {header}")
            return True, []

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error reading file: {e}")
        return False, errors

def validate_data_types(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates that data types in the CSV are correct:
    - SMILES: non-empty string
    - experimental_barrier: numeric (float)

    Args:
        file_path: Path to the CSV file to validate.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    row_count = 0
    valid_count = 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Verify columns exist first
            if reader.fieldnames is None:
                errors.append("CSV has no header.")
                return False, errors

            fieldnames = [col.strip() for col in reader.fieldnames]
            if SMILES_COLUMN not in fieldnames or BARRIER_COLUMN not in fieldnames:
                errors.append(f"Required columns not found. Expected: {REQUIRED_COLUMNS}, Found: {fieldnames}")
                return False, errors

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-based + header)
                row_count += 1

                # Validate SMILES
                smiles = row.get(SMILES_COLUMN, "").strip()
                if not smiles:
                    errors.append(f"Row {row_num}: '{SMILES_COLUMN}' is empty or missing.")
                    continue

                # Validate experimental_barrier
                barrier_str = row.get(BARRIER_COLUMN, "").strip()
                if not barrier_str:
                    errors.append(f"Row {row_num}: '{BARRIER_COLUMN}' is empty or missing.")
                    continue

                try:
                    barrier_val = float(barrier_str)
                    if barrier_val < 0:
                        errors.append(f"Row {row_num}: '{BARRIER_COLUMN}' value ({barrier_val}) is negative. Expected non-negative barrier energy.")
                        continue
                except ValueError:
                    errors.append(f"Row {row_num}: '{BARRIER_COLUMN}' value ('{barrier_str}') is not a valid number.")
                    continue

                valid_count += 1

        if row_count == 0:
            errors.append("CSV file contains no data rows.")
            return False, errors

        logger.info(f"Data type validation complete. {valid_count}/{row_count} rows valid.")
        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Unexpected error during type validation: {e}")
        return False, errors

def validate_full(file_path: Path) -> bool:
    """
    Runs all validation checks on the CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        True if all validations pass, False otherwise.

    Raises:
        ValidationError: If validation fails.
    """
    logger.info(f"Starting validation for: {file_path}")

    # Check structure
    is_valid, errors = validate_csv_structure(file_path)
    if not is_valid:
        for err in errors:
            logger.error(err)
        raise ValidationError(f"Structure validation failed: {errors}")

    # Check data types
    is_valid, errors = validate_data_types(file_path)
    if not is_valid:
        for err in errors:
            logger.error(err)
        raise ValidationError(f"Data type validation failed: {errors}")

    logger.info(f"Validation successful for {file_path}")
    return True

def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python code/validators/data_validator.py <path_to_csv>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    try:
        validate_full(csv_path)
        print("Validation PASSED.")
        sys.exit(0)
    except ValidationError as e:
        print(f"Validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()