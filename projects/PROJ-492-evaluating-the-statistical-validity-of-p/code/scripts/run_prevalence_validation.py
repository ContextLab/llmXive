"""
Script to run T042b verification: Check that prevalence.json excludes sample-size mismatch entries.

This script performs the cross-check between audit_report.json and prevalence.json
to ensure compliance with FR-004b and T025c requirements.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def load_json_file(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def identify_mismatched_records(audit_records: List[Dict[str, Any]]) -> Set[str]:
    """
    Identify record IDs that are flagged for sample-size mismatch.
    
    Checks the 'data_quality_warning' field for keywords related to sample size mismatch.
    """
    mismatch_ids = set()
    for record in audit_records:
        warnings = record.get('data_quality_warning', [])
        if isinstance(warnings, str):
            warnings = [warnings]
        
        for warning in warnings:
            warning_lower = warning.lower()
            if 'sample_size_mismatch' in warning_lower or 'sample size mismatch' in warning_lower:
                # Use ID if available, fallback to URL or index
                record_id = record.get('id') or record.get('url') or f"record_{audit_records.index(record)}"
                mismatch_ids.add(record_id)
                break
    return mismatch_ids

def get_prevalence_record_ids(prevalence_records: List[Dict[str, Any]]) -> Set[str]:
    """Extract unique IDs from prevalence records."""
    return {
        record.get('id') or record.get('url') or f"record_{prevalence_records.index(record)}"
        for record in prevalence_records
    }

def run_prevalence_exclusion_check():
    """
    Main verification logic for T042b.
    
    Returns:
        bool: True if check passes, False otherwise.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    audit_report_path = project_root / 'output' / 'audit_report.json'
    prevalence_path = project_root / 'output' / 'prevalence.json'

    logger.info(f"Starting T042b verification...")
    logger.info(f"Audit report path: {audit_report_path}")
    logger.info(f"Prevalence path: {prevalence_path}")

    # Check files exist
    if not audit_report_path.exists():
        logger.error(f"Audit report not found at {audit_report_path}. "
                    "Please run the pipeline (T025) first.")
        return False

    if not prevalence_path.exists():
        logger.error(f"Prevalence report not found at {prevalence_path}. "
                    "Please run the prevalence analysis (T042) first.")
        return False

    try:
        # Load data
        audit_records = load_json_file(audit_report_path)
        prevalence_records = load_json_file(prevalence_path)

        logger.info(f"Loaded {len(audit_records)} audit records")
        logger.info(f"Loaded {len(prevalence_records)} prevalence records")

        # Identify mismatched records
        mismatch_ids = identify_mismatched_records(audit_records)
        logger.info(f"Found {len(mismatch_ids)} records with sample-size mismatch warnings")

        # Get prevalence IDs
        prevalence_ids = get_prevalence_record_ids(prevalence_records)
        logger.info(f"Found {len(prevalence_ids)} records in prevalence analysis")

        # Check for violations
        violations = mismatch_ids.intersection(prevalence_ids)

        if violations:
            logger.error(f"VERIFICATION FAILED: {len(violations)} sample-size mismatch records found in prevalence.json")
            logger.error(f"Violating IDs: {violations}")
            return False

        logger.info("VERIFICATION PASSED: No sample-size mismatch records in prevalence.json")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def main():
    """Entry point for the script."""
    success = run_prevalence_exclusion_check()
    
    if success:
        logger.info("T042b verification completed successfully.")
        print("✓ T042b PASSED: Prevalence.json correctly excludes sample-size mismatch entries")
        sys.exit(0)
    else:
        logger.error("T042b verification failed.")
        print("✗ T042b FAILED: Prevalence.json contains sample-size mismatch entries")
        sys.exit(1)

if __name__ == '__main__':
    main()