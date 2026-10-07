"""
Task T020c: Validate sweep results from T020b against the strict outlier tolerance.

This script reads the raw Monte Carlo results (mc_results.csv), applies the
validation logic defined in T007b (using the configured OUTLIER_TOLERANCE relative
to the theoretical semicircle edge of ±2.0), and outputs a cleaned CSV file
(validated_sweep_results.csv) containing only rows that pass the validation.

It does NOT perform statistical fitting or residual analysis; that is deferred to T021c.
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_outlier_tolerance, get_project_paths
from analysis.eigen_solver import validate_eigenvalues

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_FILE = "data/processed/mc_results.csv"
OUTPUT_FILE = "data/processed/validated_sweep_results.csv"

def load_mc_results(file_path: str) -> List[Dict[str, Any]]:
    """Load the raw Monte Carlo results from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    results = []
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['N'] = int(row['N'])
                row['theta'] = float(row['theta'])
                row['seed'] = int(row['seed'])
                row['eigenvalue_top'] = float(row['eigenvalue_top'])
                # outlier_flag might be string 'True'/'False' or boolean
                if isinstance(row['outlier_flag'], str):
                    row['outlier_flag'] = row['outlier_flag'].lower() == 'true'
                else:
                    row['outlier_flag'] = bool(row['outlier_flag'])
                results.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row: {row} due to {e}")
    
    return results

def validate_row(row: Dict[str, Any], tolerance: float) -> bool:
    """
    Validate a single row against the strict tolerance.
    
    Uses the validate_eigenvalues function from T007b logic.
    The function checks if the top eigenvalue is consistent with the 
    theoretical semicircle edge (±2.0) plus the tolerance.
    
    Returns True if the row passes validation (i.e., the outlier detection 
    logic is consistent with the theoretical bounds within tolerance).
    """
    eigenvalue_top = row['eigenvalue_top']
    outlier_flag = row['outlier_flag']
    
    # The validation logic from T007b distinguishes outliers from numerical artifacts.
    # It checks if the eigenvalue is significantly beyond the semicircle edge (2.0).
    # If the eigenvalue is > 2.0 + tolerance, it is a true outlier.
    # If it is <= 2.0 + tolerance, it should NOT be flagged as an outlier.
    
    # We verify consistency:
    # If outlier_flag is True, eigenvalue_top should be > 2.0 + tolerance
    # If outlier_flag is False, eigenvalue_top should be <= 2.0 + tolerance
    
    edge = 2.0
    threshold = edge + tolerance
    
    is_true_outlier = eigenvalue_top > threshold
    
    if outlier_flag and not is_true_outlier:
        # Flagged as outlier but value is within tolerance -> numerical artifact or error
        logger.debug(f"Row {row['run_id']}: Flagged as outlier but eigenvalue {eigenvalue_top} <= {threshold}. Rejecting.")
        return False
    
    if not outlier_flag and is_true_outlier:
        # Not flagged but value is beyond tolerance -> missed detection
        logger.debug(f"Row {row['run_id']}: Not flagged but eigenvalue {eigenvalue_top} > {threshold}. Rejecting.")
        return False
    
    return True

def write_validated_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write the validated results to CSV."""
    if not results:
        logger.warning("No valid results to write.")
        # Still create an empty file with headers if needed, or just return
        # The task requires a CSV with schema, so we write headers even if empty
        fieldnames = ['run_id', 'N', 'theta', 'seed', 'eigenvalue_top', 'outlier_flag']
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return

    fieldnames = ['run_id', 'N', 'theta', 'seed', 'eigenvalue_top', 'outlier_flag']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure boolean is written as string 'True'/'False' for CSV consistency
            row_copy = row.copy()
            row_copy['outlier_flag'] = str(row_copy['outlier_flag'])
            writer.writerow(row_copy)

def main():
    paths = get_project_paths()
    input_path = paths['project_root'] / INPUT_FILE
    output_path = paths['project_root'] / OUTPUT_FILE
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist. Did T020b run?")
        sys.exit(1)

    tolerance = get_outlier_tolerance()
    logger.info(f"Loading raw results from {input_path} with tolerance {tolerance}")
    
    raw_results = load_mc_results(str(input_path))
    logger.info(f"Loaded {len(raw_results)} rows.")

    validated_results = []
    for row in raw_results:
        if validate_row(row, tolerance):
            validated_results.append(row)
    
    logger.info(f"Validation complete: {len(validated_results)} rows passed out of {len(raw_results)}.")
    
    write_validated_results(validated_results, str(output_path))
    logger.info(f"Validated results written to {output_path}")

if __name__ == "__main__":
    main()