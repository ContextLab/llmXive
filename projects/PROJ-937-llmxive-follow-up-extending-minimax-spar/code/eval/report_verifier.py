"""
Report Verifier for T036.
Verifies that results/benchmark_report.json contains all required metrics and statistical tests.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_KEYS: Set[str] = {
    'f1_score',
    'p_value',
    'false_positive_rate',
    'sensitivity_table',
    'ttest_stat',
    'wilcoxon_stat'
}

def verify_report_structure(report: Dict[str, Any], required_keys: Set[str]) -> bool:
    """
    Verify that the report contains all required top-level keys.
    
    Args:
        report: The loaded JSON report dictionary.
        required_keys: Set of required key names.
        
    Returns:
        True if all required keys are present, False otherwise.
    """
    missing_keys = required_keys - set(report.keys())
    if missing_keys:
        logger.error(f"Missing required keys in report: {missing_keys}")
        return False
    
    logger.info(f"All required keys present: {required_keys}")
    return True

def verify_sensitivity_table_structure(sensitivity_table: Any) -> bool:
    """
    Verify that the sensitivity_table is a list of dictionaries with expected structure.
    
    Args:
        sensitivity_table: The sensitivity_table field from the report.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(sensitivity_table, list):
        logger.error(f"sensitivity_table must be a list, got {type(sensitivity_table)}")
        return False
    
    if len(sensitivity_table) == 0:
        logger.warning("sensitivity_table is empty")
        return True  # Empty is technically valid structure, just no data
    
    # Check first entry structure
    sample_entry = sensitivity_table[0]
    if not isinstance(sample_entry, dict):
        logger.error(f"sensitivity_table entries must be dicts, got {type(sample_entry)}")
        return False
    
    # Expect at least threshold and metric columns
    expected_subkeys = {'threshold', 'metric_value'}
    if not expected_subkeys.issubset(sample_entry.keys()):
        logger.warning(f"sensitivity_table entries missing expected subkeys. Found: {sample_entry.keys()}")
        # Not failing strictly, just warning
    
    logger.info(f"sensitivity_table structure valid with {len(sensitivity_table)} entries")
    return True

def verify_numeric_values(report: Dict[str, Any]) -> bool:
    """
    Verify that numeric fields are actually numbers and not None or strings.
    
    Args:
        report: The loaded JSON report dictionary.
        
    Returns:
        True if all numeric fields are valid numbers, False otherwise.
    """
    numeric_fields = ['f1_score', 'p_value', 'ttest_stat', 'wilcoxon_stat']
    all_valid = True
    
    for field in numeric_fields:
        if field in report:
            value = report[field]
            if value is None:
                logger.error(f"Field '{field}' is None")
                all_valid = False
            elif not isinstance(value, (int, float)):
                logger.error(f"Field '{field}' is not numeric: {type(value)}")
                all_valid = False
            else:
                logger.info(f"Field '{field}' is valid: {value}")
        
        if 'false_positive_rate' in report:
            fpr = report['false_positive_rate']
            if fpr is None:
                logger.error("Field 'false_positive_rate' is None")
                all_valid = False
            elif not isinstance(fpr, (int, float, list)):
                # false_positive_rate can be a list if per-threshold
                logger.error(f"Field 'false_positive_rate' is not numeric or list: {type(fpr)}")
                all_valid = False
            else:
                logger.info(f"Field 'false_positive_rate' is valid")

    return all_valid

def verify_report_file_exists(report_path: Path) -> bool:
    """
    Verify that the report file exists.
    
    Args:
        report_path: Path to the report file.
        
    Returns:
        True if file exists, False otherwise.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return False
    logger.info(f"Report file found: {report_path}")
    return True

def verify_report(report_path: Path = Path("results/benchmark_report.json")) -> bool:
    """
    Main verification function for T036.
    
    Args:
        report_path: Path to the benchmark report JSON file.
        
    Returns:
        True if all verifications pass, False otherwise.
    """
    logger.info(f"Starting verification for {report_path}")
    
    # Step 1: Check file existence
    if not verify_report_file_exists(report_path):
        return False
    
    # Step 2: Load and parse JSON
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        logger.info("Report loaded successfully")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to load report: {e}")
        return False
    
    # Step 3: Verify required keys
    if not verify_report_structure(report, REQUIRED_KEYS):
        return False
    
    # Step 4: Verify sensitivity_table structure
    if 'sensitivity_table' in report:
        if not verify_sensitivity_table_structure(report['sensitivity_table']):
            return False
    
    # Step 5: Verify numeric values
    if not verify_numeric_values(report):
        return False
    
    logger.info("All verifications passed!")
    return True

def main():
    """Entry point for the verifier script."""
    report_path = Path("results/benchmark_report.json")
    success = verify_report(report_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
