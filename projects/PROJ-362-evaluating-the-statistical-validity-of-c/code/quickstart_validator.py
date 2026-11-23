"""
Quickstart Validation Script for PROJ-362.
Verifies that all required artifacts from the pipeline are generated correctly.
"""
import os
import sys
import csv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script (assuming code/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"

# Required artifacts mapping: path -> description
REQUIRED_ARTIFACTS = {
    # Data Layer
    DATA_DIR / "raw" / "qrels_robust04.json": "Raw TREC Robust04 qrels data",
    DATA_DIR / "raw" / "qrels_web.json": "Raw TREC Web qrels data",
    
    # Null Distributions (US1)
    "results/null_distributions": "Directory containing null distribution CSVs",
    
    # P-Values (US1)
    "results/p_values/raw_p_values.csv": "Raw p-values for all queries",
    
    # MDES (US2)
    "results/mdes/mdes_summary.csv": "MDES summary with power analysis",
    
    # Corrected P-Values (US2)
    "results/p_values/corrected_p_values.csv": "BH-corrected p-values",
    
    # Sensitivity Analysis (US2)
    "results/sensitivity/alpha_sweep.csv": "Sensitivity analysis across alpha values",
    
    # Visualization (US3)
    "results/plots": "Directory containing density plots (PNG)",
    
    # Final Summary (US3)
    "results/summary.csv": "Aggregated summary of all metrics and p-values",
}

# Required columns for CSV files
REQUIRED_CSV_COLUMNS = {
    "results/p_values/raw_p_values.csv": ["query_id", "metric", "p_value"],
    "results/mdes/mdes_summary.csv": ["metric", "mdes", "power", "ci_width"],
    "results/p_values/corrected_p_values.csv": ["query_id", "metric", "raw_p", "corrected_p", "is_significant"],
    "results/sensitivity/alpha_sweep.csv": ["alpha", "significant_count"],
    "results/summary.csv": ["query_id", "metric", "observed_score", "raw_p", "corrected_p", "mdes", "is_significant"],
}

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file or directory exists."""
    if not path.exists():
        logger.error(f"MISSING: {description} at {path}")
        return False
    logger.info(f"FOUND: {description} at {path}")
    return True

def validate_csv_columns(file_path: Path, required_columns: list) -> bool:
    """Validate that a CSV file has the required columns."""
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error(f"EMPTY OR INVALID: {file_path} has no headers")
                return False
            
            missing = set(required_columns) - set(reader.fieldnames)
            if missing:
                logger.error(f"INVALID COLUMNS in {file_path}: Missing {missing}")
                return False
            
            # Check if file has at least one data row
            rows = list(reader)
            if len(rows) == 0:
                logger.warning(f"WARNING: {file_path} has headers but no data rows")
                # This might be acceptable depending on context, but log it
            else:
                logger.info(f"VALID: {file_path} has {len(rows)} data rows with correct columns")
            return True
    except Exception as e:
        logger.error(f"ERROR reading {file_path}: {e}")
        return False

def run_validation() -> bool:
    """Run the full validation suite."""
    logger.info("Starting Quickstart Validation for PROJ-362")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    
    all_passed = True
    
    # Check all artifacts
    for path_str, description in REQUIRED_ARTIFACTS.items():
        path = path_str if isinstance(path_str, Path) else PROJECT_ROOT / path_str
        if not check_file_exists(path, description):
            all_passed = False
    
    # Validate CSV columns
    for path_str, columns in REQUIRED_CSV_COLUMNS.items():
        file_path = PROJECT_ROOT / path_str
        if file_path.exists():
            if not validate_csv_columns(file_path, columns):
                all_passed = False
        else:
            logger.warning(f"SKIPPING column validation for {path_str} (file not found)")
    
    # Summary
    logger.info("=" * 50)
    if all_passed:
        logger.info("VALIDATION PASSED: All required artifacts are present and valid.")
        return True
    else:
        logger.error("VALIDATION FAILED: Some artifacts are missing or invalid.")
        return False

def main():
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
