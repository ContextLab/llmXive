import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Set

# Import logger from existing API
from utils.logger import get_logger_for_task

REQUIRED_KEYS: Set[str] = {
    "f1_score",
    "p_value",
    "false_positive_rate",
    "sensitivity_table",
    "ttest_stat",
    "wilcoxon_stat",
    "significance_statement"
}

def verify_report_file_exists(report_path: Path) -> bool:
    """Check if the benchmark report file exists on disk."""
    if not report_path.exists():
        logging.error(f"Report file not found: {report_path}")
        return False
    return True

def verify_report_structure(report_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Verify that the report dictionary contains all required keys.
    Returns (is_valid, list_of_missing_keys).
    """
    missing_keys = []
    for key in REQUIRED_KEYS:
        if key not in report_data:
            missing_keys.append(key)
    
    if missing_keys:
        logging.error(f"Missing required keys in report: {missing_keys}")
        return False, missing_keys
    
    logging.info("All required top-level keys present in report.")
    return True, []

def verify_sensitivity_table_structure(report_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Verify that the sensitivity_table is a list of dicts with expected numeric keys.
    """
    missing_keys = []
    sensitivity_table = report_data.get("sensitivity_table")
    
    if not isinstance(sensitivity_table, list):
        logging.error("sensitivity_table must be a list.")
        return False, ["sensitivity_table (must be list)"]
    
    if len(sensitivity_table) == 0:
        logging.warning("sensitivity_table is empty.")
        # Not strictly a failure of structure, but log warning
        return True, []

    required_table_keys = {"threshold", "accuracy", "false_positive_rate"}
    
    for i, entry in enumerate(sensitivity_table):
        if not isinstance(entry, dict):
            logging.error(f"sensitivity_table entry {i} is not a dict.")
            missing_keys.append(f"sensitivity_table[{i}]")
            continue
        
        entry_keys = set(entry.keys())
        if not required_table_keys.issubset(entry_keys):
            missing_in_entry = required_table_keys - entry_keys
            logging.error(f"sensitivity_table entry {i} missing keys: {missing_in_entry}")
            missing_keys.append(f"sensitivity_table[{i}] keys: {missing_in_entry}")
        
        # Check numeric types
        for k in required_table_keys:
            val = entry.get(k)
            if val is not None and not isinstance(val, (int, float)):
                logging.error(f"sensitivity_table entry {i} key '{k}' is not numeric.")
                missing_keys.append(f"sensitivity_table[{i}].{k} (non-numeric)")

    if missing_keys:
        return False, missing_keys
    
    logging.info("Sensitivity table structure verified.")
    return True, []

def verify_numeric_values(report_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Verify that specific top-level fields are numeric.
    """
    numeric_fields = ["f1_score", "p_value", "ttest_stat", "wilcoxon_stat"]
    missing_keys = []
    
    for field in numeric_fields:
        val = report_data.get(field)
        if val is None:
            # Should have been caught by structure check, but double check
            missing_keys.append(f"{field} (missing)")
            continue
        
        if not isinstance(val, (int, float)):
            logging.error(f"Field '{field}' is not numeric: {type(val)}")
            missing_keys.append(f"{field} (non-numeric)")
    
    if missing_keys:
        return False, missing_keys
    
    logging.info("Numeric values verified.")
    return True, []

def verify_report(report_path: Path) -> bool:
    """
    Main entry point to verify the benchmark report.
    Returns True if the report is valid, False otherwise.
    """
    logger = get_logger_for_task("T036")
    
    if not verify_report_file_exists(report_path):
        return False
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report: {e}")
        return False
    
    # 1. Check top-level structure
    is_valid, missing = verify_report_structure(report_data)
    if not is_valid:
        return False
    
    # 2. Check sensitivity table structure
    is_valid, missing = verify_sensitivity_table_structure(report_data)
    if not is_valid:
        return False
    
    # 3. Check numeric values
    is_valid, missing = verify_numeric_values(report_data)
    if not is_valid:
        return False
    
    logger.info("Benchmark report verification PASSED.")
    return True

def main():
    """CLI entry point for verification."""
    report_path = Path("results/benchmark_report.json")
    
    if not verify_report(report_path):
        print("Verification FAILED.")
        sys.exit(1)
    else:
        print("Verification SUCCESS.")
        sys.exit(0)

if __name__ == "__main__":
    main()