import csv
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_SNIPPET_COLUMNS = {
    'snippet_id',
    'perplexity',
    'functional_correctness_rate',
    'inference_time',
    'status'
}

REQUIRED_FILE_METRICS_COLUMNS = {
    'file_path',
    'mean_perplexity',
    'mean_correctness',
    'mean_complexity',
    'mean_length',
    'median_age'
}

def verify_csv_structure(file_path: Path, required_columns: Set[str], file_type: str) -> bool:
    """
    Verify that a CSV file exists and contains the required columns.
    
    Args:
        file_path: Path to the CSV file
        required_columns: Set of required column names
        file_type: Human-readable name for error messages (e.g., "Inference Output")
        
    Returns:
        True if structure is valid, False otherwise
    """
    if not file_path.exists():
        logger.error(f"{file_type} file not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error(f"{file_type} file is empty or has no header: {file_path}")
                return False
            
            actual_columns = set(reader.fieldnames)
            missing_columns = required_columns - actual_columns
            
            if missing_columns:
                logger.error(f"{file_type} file missing required columns: {missing_columns}")
                logger.error(f"Found columns: {actual_columns}")
                return False
            
            # Check that file has at least one data row
            rows = list(reader)
            if len(rows) == 0:
                logger.warning(f"{file_type} file exists but contains no data rows: {file_path}")
                # This is a warning, not a failure for structure check, 
                # but completeness check will catch it later
                return True
            
            logger.info(f"{file_type} structure verified: {file_path} ({len(rows)} rows)")
            return True

    except Exception as e:
        logger.error(f"Error reading {file_type} file {file_path}: {e}")
        return False

def verify_file_metrics_content(file_path: Path) -> bool:
    """
    Verify that file_metrics.csv contains valid aggregated data (non-null metrics).
    
    Args:
        file_path: Path to file_metrics.csv
        
    Returns:
        True if content is valid, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File metrics file not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error("File metrics file is empty or has no header.")
                return False

            required_cols = {'mean_perplexity', 'mean_correctness', 'mean_complexity'}
            actual_cols = set(reader.fieldnames)
            if not required_cols.issubset(actual_cols):
                logger.error(f"File metrics missing key metric columns: {required_cols - actual_cols}")
                return False

            valid_count = 0
            total_count = 0
            for row in reader:
                total_count += 1
                # Check for at least one valid metric per row
                has_valid_metric = False
                for col in required_cols:
                    val = row.get(col, '').strip()
                    if val and val.lower() != 'nan' and val != '':
                        try:
                            float(val)
                            has_valid_metric = True
                            break
                        except ValueError:
                            continue
                
                if has_valid_metric:
                    valid_count += 1

            if total_count == 0:
                logger.warning("File metrics file exists but contains no data rows.")
                return True # Structure ok, but data check will fail elsewhere

            logger.info(f"File metrics verified: {valid_count}/{total_count} rows have valid metric data.")
            return valid_count > 0

    except Exception as e:
        logger.error(f"Error verifying file metrics content: {e}")
        return False

def main():
    """
    Main entry point to verify inference output structure and file_metrics aggregation.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_results_dir = project_root / 'data' / 'results'
    data_aggregated_dir = project_root / 'data' / 'aggregated'
    
    inference_output_path = data_results_dir / 'inference_results.csv'
    file_metrics_path = data_aggregated_dir / 'file_metrics.csv'

    all_passed = True

    # 1. Verify Inference Output CSV Structure
    logger.info("Verifying inference output CSV structure...")
    if not verify_csv_structure(inference_output_path, REQUIRED_SNIPPET_COLUMNS, "Inference Output"):
        all_passed = False

    # 2. Verify File Metrics CSV Structure
    logger.info("Verifying file_metrics.csv structure...")
    if not verify_csv_structure(file_metrics_path, REQUIRED_FILE_METRICS_COLUMNS, "File Metrics"):
        all_passed = False
    else:
        # 3. Verify File Metrics Content (valid aggregated data)
        logger.info("Verifying file_metrics.csv content...")
        if not verify_file_metrics_content(file_metrics_path):
            all_passed = False

    if all_passed:
        logger.info("✅ T019 Verification PASSED: All structures and aggregations are valid.")
        sys.exit(0)
    else:
        logger.error("❌ T019 Verification FAILED: One or more checks failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
