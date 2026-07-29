from __future__ import annotations
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Tuple

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "results/plots",
    "tests/unit",
    "tests/integration",
    "state"
]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "data/processed/simulation_results.csv",
    "results/final_report.md",
    "results/sensitivity_report.csv"
]

REQUIRED_COLUMNS_SIM_RESULTS = [
    "dataset_id",
    "dataset_name",
    "method",
    "snr",
    "sparsity",
    "power_rate",
    "true_positives",
    "false_positives",
    "selected_vars",
    "true_nonzero_count"
]

def check_directories() -> Tuple[bool, List[str]]:
    """Verify all required directories exist."""
    missing = []
    for dir_name in REQUIRED_DIRS:
        path = PROJECT_ROOT / dir_name
        if not path.exists():
            missing.append(str(path))
        elif not path.is_dir():
            missing.append(f"{path} (not a directory)")
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False, missing
    
    logger.info("All required directories exist.")
    return True, []

def check_files() -> Tuple[bool, List[str]]:
    """Verify all required files exist."""
    missing = []
    for file_name in REQUIRED_FILES:
        path = PROJECT_ROOT / file_name
        if not path.exists():
            missing.append(str(path))
    
    if missing:
        logger.error(f"Missing files: {missing}")
        return False, missing
    
    logger.info("All required files exist.")
    return True, []

def check_simulation_results_integrity() -> Tuple[bool, str]:
    """Verify simulation_results.csv has content and correct columns."""
    file_path = PROJECT_ROOT / "data/processed/simulation_results.csv"
    if not file_path.exists():
        return False, "simulation_results.csv not found"
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, "CSV has no headers"
            
            missing_cols = [col for col in REQUIRED_COLUMNS_SIM_RESULTS if col not in headers]
            if missing_cols:
                return False, f"Missing columns: {missing_cols}"
            
            row_count = 0
            for row in reader:
                row_count += 1
                # Check for null dataset_id or dataset_name as per T054
                if not row.get('dataset_id') or not row.get('dataset_name'):
                    return False, f"Row {row_count} has null dataset_id or dataset_name"
            
            if row_count == 0:
                return False, "CSV is empty (0 rows)"
            
            logger.info(f"simulation_results.csv validated: {row_count} rows, all required columns present.")
            return True, f"Validated {row_count} rows"
    
    except Exception as e:
        logger.error(f"Error reading simulation_results.csv: {e}")
        return False, str(e)

def check_imports() -> Tuple[bool, str]:
    """Verify critical modules can be imported without error."""
    critical_modules = [
        "config",
        "models",
        "data.downloader",
        "data.simulators",
        "data.storage",
        "analysis.selectors",
        "analysis.metrics",
        "analysis.comparators",
        "viz.plots",
        "utils.logger",
        "utils.limits"
    ]
    
    failed_imports = []
    for mod in critical_modules:
        try:
            __import__(mod)
        except ImportError as e:
            failed_imports.append(f"{mod}: {e}")
        except Exception as e:
            failed_imports.append(f"{mod}: {type(e).__name__}: {e}")
    
    if failed_imports:
        logger.error(f"Import failures: {failed_imports}")
        return False, "; ".join(failed_imports)
    
    logger.info("All critical modules imported successfully.")
    return True, "All imports OK"

def main():
    """Run all quickstart validation checks."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T048)")
    logger.info("=" * 60)
    
    all_passed = True
    
    # 1. Check Directories
    success, errors = check_directories()
    if not success:
        all_passed = False
    
    # 2. Check Files
    success, errors = check_files()
    if not success:
        all_passed = False
    
    # 3. Check Simulation Results Integrity
    success, msg = check_simulation_results_integrity()
    if not success:
        all_passed = False
    else:
        logger.info(f"Integrity Check: {msg}")
    
    # 4. Check Imports
    success, msg = check_imports()
    if not success:
        all_passed = False
    else:
        logger.info(f"Import Check: {msg}")
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("VALIDATION PASSED: Project structure and artifacts are valid.")
        return 0
    else:
        logger.error("VALIDATION FAILED: See errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
