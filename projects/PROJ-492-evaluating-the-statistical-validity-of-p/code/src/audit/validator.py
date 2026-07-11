"""
Validator module for T025: Inconsistency validation and T025b: Missing baseline flagging.
Implements FR-004 thresholds and FR-012 missing data flagging.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message, AuditLogger
from code.src.config import SEED

logger = get_default_logger(__name__)

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validates a single ABTestSummary against its reconstructed statistical values.
    Flags inconsistencies and missing data as per FR-004 and FR-012.

    Args:
        summary: The extracted ABTestSummary object.
        reconstructed: Dictionary of reconstructed statistical values.

    Returns:
        AuditRecord with flags and notes.
    """
    notes = []
    data_quality_warning = None
    is_inconsistent = False

    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes.append("Missing baseline conversion rate. Statistical reconstruction may be incomplete.")
        data_quality_warning = "Missing baseline data"
        # We do not mark as statistically inconsistent due to missing data,
        # but we flag the data quality issue.
    else:
        # Check for missing treatment rate as well
        if summary.conversion_rate_treatment is None:
            notes.append("Missing treatment conversion rate.")
            data_quality_warning = "Missing treatment data"

    # FR-004: Check for sample size mismatches
    if (summary.sample_size_control is not None and summary.sample_size_treatment is not None and
        reconstructed.get('sample_size_control') is not None and reconstructed.get('sample_size_treatment') is not None):
        if summary.sample_size_control != reconstructed['sample_size_control'] or \
           summary.sample_size_treatment != reconstructed['sample_size_treatment']:
            notes.append("Sample size mismatch between reported and reconstructed data.")
            data_quality_warning = "Sample size mismatch"
            # Per FR-004b, this is a data quality warning, not necessarily a statistical inconsistency
            # unless it leads to p-value discrepancies.

    # Statistical consistency checks (only if data is present)
    if summary.conversion_rate_control is not None and summary.conversion_rate_treatment is not None:
        p_reported = summary.p_value_reported
        p_reconstructed = reconstructed.get('p_value_reconstructed')

        if p_reported is not None and p_reconstructed is not None:
            # Absolute p-difference > 0.05 threshold
            if abs(p_reported - p_reconstructed) > 0.05:
                notes.append(f"P-value discrepancy: reported={p_reported:.4f}, reconstructed={p_reconstructed:.4f}")
                is_inconsistent = True

            # Relative effect-size > 5% threshold
            effect_reported = summary.effect_size_reported
            effect_reconstructed = reconstructed.get('effect_size_reconstructed')

            if effect_reported is not None and effect_reconstructed is not None and effect_reported != 0:
                rel_diff = abs(effect_reported - effect_reconstructed) / abs(effect_reported)
                if rel_diff > 0.05:
                    notes.append(f"Effect size discrepancy: reported={effect_reported:.4f}, reconstructed={effect_reconstructed:.4f}")
                    is_inconsistent = True

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        notes=" ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        publication_year=summary.publication_year
    )

def validate_all_records(summaries: List[ABTestSummary], reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validates a list of ABTestSummary objects against their reconstructed values.

    Args:
        summaries: List of ABTestSummary objects.
        reconstructed_list: List of reconstructed value dictionaries.

    Returns:
        List of AuditRecord objects.
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError("Number of summaries and reconstructed records must match.")

    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)

    return audit_records

def main():
    """
    Main entry point for running validation on a dataset.
    Expects input JSON files and writes audit report.
    """
    # This is a placeholder for the actual CLI execution logic
    # The test suite T025b validates the core logic of validate_single_record
    logger.info("Validator module loaded. Run specific validation tasks via test suite or CLI.")

if __name__ == "__main__":
    main()
