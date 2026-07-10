"""
T016: Verify all rows in output CSV have valid numeric values for all three metrics.

This script validates the output of T015 (data/processed/annotated_metrics.csv) to ensure:
1. All rows contain valid numeric values for Cyclomatic Complexity, Halstead Volume, and Maintainability Index.
2. No rows contain NaN, Inf, or non-numeric strings in these columns.
3. The verification report is logged and saved to data/processed/verification_report.json.

SC-004 Compliance: Ensures data integrity before downstream analysis.
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_deterministic_logging, get_logger, set_seed

# Configuration
INPUT_CSV_PATH = project_root / "data" / "processed" / "annotated_metrics.csv"
METADATA_PATH = project_root / "data" / "processed" / "metadata.json"
VERIFICATION_REPORT_PATH = project_root / "data" / "processed" / "verification_report.json"

REQUIRED_METRICS = [
    "cyclomatic_complexity",
    "halstead_volume",
    "maintainability_index"
]

def load_metadata() -> Dict[str, Any]:
    """Load metadata from metadata.json."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Metadata file not found: {METADATA_PATH}")
    
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_numeric_value(value: Any, metric_name: str) -> bool:
    """
    Validate that a value is a valid finite number.
    Returns True if valid, False otherwise.
    """
    if value is None:
        return False
    
    try:
        num = float(value)
        # Check for NaN or Inf
        if num != num:  # NaN check
            return False
        if num == float('inf') or num == float('-inf'):
            return False
        return True
    except (ValueError, TypeError):
        return False

def verify_csv_metrics() -> Dict[str, Any]:
    """
    Verify all rows in the annotated_metrics.csv have valid numeric values.
    
    Returns a verification report dictionary.
    """
    if not INPUT_CSV_PATH.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV_PATH}")
    
    logger.info(f"Starting verification of {INPUT_CSV_PATH}")
    
    total_rows = 0
    valid_rows = 0
    invalid_rows: List[Dict[str, Any]] = []
    metric_failures: Dict[str, int] = {metric: 0 for metric in REQUIRED_METRICS}
    
    with open(INPUT_CSV_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        
        # Validate header
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers")
        
        missing_metrics = [m for m in REQUIRED_METRICS if m not in reader.fieldnames]
        if missing_metrics:
            raise ValueError(f"Missing required metric columns: {missing_metrics}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            total_rows += 1
            row_valid = True
            row_issues = []
            
            for metric in REQUIRED_METRICS:
                value = row.get(metric)
                if not validate_numeric_value(value, metric):
                    row_valid = False
                    metric_failures[metric] += 1
                    row_issues.append({
                        "metric": metric,
                        "value": value,
                        "issue": "Invalid numeric value (NaN, Inf, or non-numeric)"
                    })
            
            if row_valid:
                valid_rows += 1
            else:
                invalid_rows.append({
                    "row_number": row_num,
                    "snippet_id": row.get("snippet_id", "UNKNOWN"),
                    "issues": row_issues
                })
                
                # Limit stored invalid rows to prevent huge logs
                if len(invalid_rows) >= 100:
                    logger.warning(f"Stopping detailed error collection after 100 invalid rows")
                    break
    
    # Calculate statistics
    pass_rate = (valid_rows / total_rows * 100) if total_rows > 0 else 0.0
    is_passed = (pass_rate == 100.0) and (total_rows > 0)
    
    report = {
        "verification_timestamp": datetime.utcnow().isoformat() + "Z",
        "input_file": str(INPUT_CSV_PATH),
        "total_rows_checked": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows_count": len(invalid_rows),
        "pass_rate_percent": round(pass_rate, 4),
        "is_passed": is_passed,
        "metric_failure_counts": metric_failures,
        "sample_invalid_rows": invalid_rows[:10] if invalid_rows else [],
        "status": "PASSED" if is_passed else "FAILED"
    }
    
    logger.info(f"Verification complete: {total_rows} rows, {valid_rows} valid, {len(invalid_rows)} invalid")
    logger.info(f"Pass rate: {pass_rate:.4f}%")
    logger.info(f"Status: {'PASSED' if is_passed else 'FAILED'}")
    
    return report

def main():
    """Main entry point for T016 verification."""
    # Setup logging
    logger = setup_deterministic_logging("T016_Metrics_Verification")
    set_seed(42)  # Deterministic execution
    
    logger.info("=" * 60)
    logger.info("Starting T016: Metrics Verification (SC-004)")
    logger.info("=" * 60)
    
    try:
        # Load metadata for context
        metadata = load_metadata()
        logger.info(f"Metadata loaded: {metadata.get('total_valid_snippets', 'N/A')} valid snippets expected")
        
        # Run verification
        report = verify_csv_metrics()
        
        # Save report
        with open(VERIFICATION_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification report saved to: {VERIFICATION_REPORT_PATH}")
        
        # Exit with appropriate code
        if report["is_passed"]:
            logger.info("✅ All rows have valid numeric values. Verification PASSED.")
            sys.exit(0)
        else:
            logger.error("❌ Verification FAILED. Invalid data detected.")
            logger.error(f"   Invalid rows: {report['invalid_rows_count']}")
            logger.error(f"   Pass rate: {report['pass_rate_percent']:.4f}%")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()