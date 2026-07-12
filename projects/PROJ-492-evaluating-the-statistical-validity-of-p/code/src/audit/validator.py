"""
Validator module for T025: Implements inconsistency validation logic.
Specifically handles FR-012: Flagging missing baseline conversion rates.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message, AuditLogger
from code.src.config import SEED

logger = get_default_logger(__name__)

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validates a single ABTestSummary against its reconstructed values.
    Implements FR-004 (thresholds) and FR-012 (missing baseline flag).

    Args:
        summary: The extracted summary object.
        reconstructed: Dictionary containing reconstructed statistical values.

    Returns:
        An AuditRecord object with flags and notes.
    """
    notes = []
    data_quality_warning = None
    is_inconsistent = False

    # --- FR-012: Check for Missing Baseline Conversion Rate ---
    if summary.test_type == "binary":
        if summary.conversion_rate_control is None:
            notes.append("missing baseline conversion rate")
            data_quality_warning = "Missing baseline conversion rate prevents full statistical reconstruction per FR-012."
            logger.warning(f"Missing baseline for {summary.url}: {data_quality_warning}")
        elif summary.conversion_rate_treatment is None:
            notes.append("missing treatment conversion rate")
            if data_quality_warning is None:
                data_quality_warning = "Missing treatment conversion rate."
    
    # --- FR-004: Statistical Inconsistency Checks ---
    if summary.conversion_rate_control is not None and summary.conversion_rate_treatment is not None:
        reported_p = summary.p_value_reported
        reconstructed_p = reconstructed.get("p_value")
        
        if reported_p is not None and reconstructed_p is not None:
            # Absolute p-value difference check (> 0.05)
            if abs(reported_p - reconstructed_p) > 0.05:
                notes.append(f"p-value discrepancy > 0.05 (reported: {reported_p}, reconstructed: {reconstructed_p})")
                is_inconsistent = True

            # Effect size check (relative > 5%)
            reported_effect = summary.effect_size_reported
            reconstructed_effect = reconstructed.get("effect_size")
            
            if reported_effect is not None and reconstructed_effect is not None:
                if reported_effect != 0:
                    rel_diff = abs(reported_effect - reconstructed_effect) / abs(reported_effect)
                    if rel_diff > 0.05:
                        notes.append(f"Effect size discrepancy > 5% (reported: {reported_effect}, reconstructed: {reconstructed_effect})")
                        is_inconsistent = True

    # --- Sample Size Mismatch Check (FR-004b) ---
    # Assuming reconstructed might contain expected sample sizes if derived differently
    # For now, we flag if sample sizes are missing or zero
    if summary.sample_size_control == 0 or summary.sample_size_treatment == 0:
        notes.append("Sample size mismatch or zero detected")
        data_quality_warning = "Invalid sample sizes detected."

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        notes="; ".join(notes) if notes else "",
        data_quality_warning=data_quality_warning,
        publication_year=summary.publication_year,
        test_type=summary.test_type
    )

def validate_all_records(summaries: List[ABTestSummary], reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validates a list of summaries against their reconstructed values.

    Args:
        summaries: List of ABTestSummary objects.
        reconstructed_list: List of reconstructed dictionaries.

    Returns:
        List of AuditRecord objects.
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError("Number of summaries must match number of reconstructed records")

    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
    
    return audit_records

def main():
    """
    Main entry point for running the validator on a dataset.
    Expected to be called by the driver script.
    """
    logger.info("Validator module loaded. Run via driver script.")

if __name__ == "__main__":
    main()