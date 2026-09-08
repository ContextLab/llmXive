"""
Task T020b: VALIDATION of sweep results.

Applies the 1e-10 outlier validation logic (from T007b) to the sweep results
in `data/processed/mc_results.csv` to ensure every data point meets the spec's
strict tolerance before fitting. Outputs validated results to
`data/processed/validated_sweep_results.csv`.
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the validation logic from the established API surface (T007b)
from analysis.eigen_solver import validate_eigenvalues
from utils.config import get_project_paths, get_tolerance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_mc_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the Monte Carlo results from a CSV file.

    Args:
        input_path: Path to the mc_results.csv file.

    Returns:
        List of dictionaries representing each row in the CSV.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['N'] = int(row['N'])
                row['theta'] = float(row['theta'])
                row['seed'] = int(row['seed'])
                row['rank'] = int(row['rank'])
                row['support_density'] = float(row['support_density'])
                row['eigenvalues'] = json.loads(row['eigenvalues'])
                if 'outlier_flag' in row:
                    row['outlier_flag'] = row['outlier_flag'].lower() == 'true'
                if 'max_eigenvalue' in row:
                    row['max_eigenvalue'] = float(row['max_eigenvalue'])
                if 'solver_residual' in row:
                    row['solver_residual'] = float(row['solver_residual'])
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                logger.warning(f"Skipping malformed row: {row} due to {e}")
                continue
            results.append(row)

    logger.info(f"Loaded {len(results)} rows from {input_path}")
    return results

def validate_row(row: Dict[str, Any], tolerance: float = 1e-10) -> Dict[str, Any]:
    """
    Apply the 1e-10 outlier validation logic to a single row.

    This function uses the `validate_eigenvalues` function from T007b to
    distinguish outliers from numerical artifacts using a strict tolerance
    relative to the theoretical semicircle edge (±2.0).

    Args:
        row: A dictionary representing a single row from mc_results.csv.
        tolerance: The tolerance threshold for validation (default 1e-10).

    Returns:
        The row dictionary updated with validation results.
    """
    eigenvalues = row.get('eigenvalues', [])
    theta = row.get('theta', 0.0)
    N = row.get('N', 0)
    rank = row.get('rank', 0)

    if not eigenvalues:
        row['validation_status'] = 'failed_no_eigenvalues'
        row['is_valid'] = False
        return row

    # Call the validation logic from T007b
    # validate_eigenvalues returns (is_outlier, details_dict)
    try:
        is_outlier, details = validate_eigenvalues(eigenvalues, theta, N, rank, tolerance=tolerance)
        
        row['validation_status'] = 'passed' if is_outlier else 'failed_no_outlier'
        row['is_valid'] = is_outlier
        
        # Store detailed validation info if available
        if details:
            row['validation_details'] = json.dumps(details)
            
    except Exception as e:
        logger.error(f"Validation failed for row {row.get('run_id', 'unknown')}: {e}")
        row['validation_status'] = f'error_{str(e)}'
        row['is_valid'] = False

    return row

def write_validated_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the validated results to a CSV file.

    Args:
        results: List of validated row dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to write.")
        # Create an empty file with headers to indicate completion
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['run_id', 'N', 'theta', 'seed', 'rank', 'support_density', 
                             'eigenvalues', 'outlier_flag', 'max_eigenvalue', 'is_valid', 'validation_status'])
        return

    # Determine all unique keys to ensure consistent headers
    fieldnames = set()
    for row in results:
        fieldnames.update(row.keys())
    
    # Define a standard order for important columns
    standard_order = [
        'run_id', 'N', 'theta', 'seed', 'rank', 'support_density', 
        'eigenvalues', 'outlier_flag', 'max_eigenvalue', 'is_valid', 'validation_status'
    ]
    
    # Add any extra columns not in the standard order
    extra_fields = sorted([f for f in fieldnames if f not in standard_order])
    fieldnames = standard_order + extra_fields

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info(f"Wrote {len(results)} validated rows to {output_path}")

def main() -> int:
    """
    Main entry point for Task T020b.

    Reads mc_results.csv, applies validation, and writes validated_sweep_results.csv.
    """
    project_paths = get_project_paths()
    input_path = project_paths / "data" / "processed" / "mc_results.csv"
    output_path = project_paths / "data" / "processed" / "validated_sweep_results.csv"
    tolerance = get_tolerance()

    logger.info(f"Starting validation of sweep results.")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Validation tolerance: {tolerance}")

    try:
        # Load raw results
        results = load_mc_results(input_path)
        
        if not results:
            logger.warning("No valid rows found in input file. Creating empty output.")
            write_validated_results([], output_path)
            return 0

        # Validate each row
        validated_results = []
        valid_count = 0
        invalid_count = 0
        error_count = 0

        for row in results:
            validated_row = validate_row(row, tolerance)
            validated_results.append(validated_row)
            
            if validated_row.get('is_valid'):
                valid_count += 1
            elif 'error' in validated_row.get('validation_status', ''):
                error_count += 1
            else:
                invalid_count += 1

        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid, {error_count} errors.")
        
        # Write results
        write_validated_results(validated_results, output_path)
        
        logger.info(f"Task T020b completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())