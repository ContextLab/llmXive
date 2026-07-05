"""
Integration test for T037: FR-003 Verification.
Asserts that reconstructed p-values are computed for all records in the audit report.

This test verifies that the reconstructor module successfully processes every
summary in the audit dataset and produces a non-null p-value in the resulting
AuditRecord.
"""
import csv
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.validator import validate_all_summaries, write_audit_report
from code.src.audit.reconstructor import reconstruct_all
from code.src.models.data_models import ABTestSummary, AuditRecord

logger = get_default_logger("test_reconstructor_completeness")

def load_synthetic_summaries(file_path: Path) -> List[Dict[str, Any]]:
    """Load synthetic summaries from the generated CSV."""
    summaries = []
    if not file_path.exists():
        raise FileNotFoundError(f"Synthetic dataset not found at {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            summaries.append(row)
    return summaries

def run_completeness_check() -> bool:
    """
    Run the reconstruction pipeline on the synthetic dataset and verify
    that every record has a computed p-value.
    
    Returns:
        bool: True if all records have p-values, False otherwise.
    """
    data_dir = PROJECT_ROOT / "data" / "synthetic"
    input_file = data_dir / "synthetic_validation.csv"
    output_file = PROJECT_ROOT / "output" / "audit_report.json"
    
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True)

    logger.info(f"Loading synthetic data from {input_file}")
    raw_summaries = load_synthetic_summaries(input_file)
    logger.info(f"Loaded {len(raw_summaries)} summaries")

    if not raw_summaries:
        logger.error("No summaries found in input file.")
        return False

    # Convert raw dicts to ABTestSummary objects
    ab_summaries: List[ABTestSummary] = []
    for i, row in enumerate(raw_summaries):
        try:
            # Map CSV columns to ABTestSummary fields based on synthetic generator logic
            # The synthetic generator typically produces: n_control, n_treatment, 
            # success_control, success_treatment, p_value_reported, effect_size_reported
            summary = ABTestSummary(
                url=f"synthetic_url_{i}",
                n_control=int(row.get('n_control', 0)),
                n_treatment=int(row.get('n_treatment', 0)),
                success_control=float(row.get('success_control', 0)),
                success_treatment=float(row.get('success_treatment', 0)),
                p_value_reported=float(row.get('p_value_reported', 0.0)),
                effect_size_reported=float(row.get('effect_size_reported', 0.0)),
                outcome_type=row.get('outcome_type', 'binary')
            )
            ab_summaries.append(summary)
        except Exception as e:
            logger.warning(f"Skipping malformed summary row {i}: {e}")

    if not ab_summaries:
        logger.error("No valid ABTestSummary objects created.")
        return False

    # Run reconstruction
    logger.info("Running reconstruction on all summaries...")
    reconstructed_records = reconstruct_all(ab_summaries)
    
    logger.info(f"Reconstructed {len(reconstructed_records)} records")

    # Validate completeness
    missing_pvalue_count = 0
    missing_pvalue_indices = []

    for idx, record in enumerate(reconstructed_records):
        if record.p_value_reconstructed is None:
            missing_pvalue_count += 1
            missing_pvalue_indices.append(idx)

    if missing_pvalue_count > 0:
        logger.error(f"FAILED: {missing_pvalue_count} records are missing reconstructed p-values.")
        logger.error(f"Indices with missing p-values: {missing_pvalue_indices[:10]}...")
        return False

    logger.info("SUCCESS: All records have a reconstructed p-value.")
    
    # Write the audit report to disk for downstream verification
    write_audit_report(reconstructed_records, output_file)
    logger.info(f"Audit report written to {output_file}")

    return True

def main():
    """Main entry point for the integration test."""
    logger.info("Starting T037: Reconstructor Completeness Verification")
    
    try:
        success = run_completeness_check()
        if success:
            logger.info("T037 PASSED: All records have reconstructed p-values.")
            sys.exit(0)
        else:
            logger.error("T037 FAILED: Some records missing p-values.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"T037 FAILED with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()