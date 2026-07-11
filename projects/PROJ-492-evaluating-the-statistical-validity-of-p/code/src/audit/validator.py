"""
Inconsistency validator for A/B test summaries.
Applies FR-004 thresholds and flags data quality issues per FR-012.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message, AuditLogger
from code.src.config import SEED

logger = get_default_logger(__name__)

def calculate_p_value_diff(p_reported: Optional[float], p_reconstructed: Optional[float]) -> Optional[float]:
    """Calculate absolute difference between reported and reconstructed p-values."""
    if p_reported is None or p_reconstructed is None:
        return None
    return abs(p_reported - p_reconstructed)

def calculate_effect_size_diff(
    effect_reported: Optional[float],
    effect_reconstructed: Optional[float]
) -> Optional[float]:
    """Calculate absolute difference between reported and reconstructed effect sizes."""
    if effect_reported is None or effect_reconstructed is None:
        return None
    return abs(effect_reported - effect_reconstructed)

def calculate_relative_effect_size_diff(
    effect_reported: Optional[float],
    effect_reconstructed: Optional[float]
) -> Optional[float]:
    """Calculate relative difference in effect sizes."""
    if effect_reported is None or effect_reconstructed is None:
        return None
    if effect_reported == 0:
        return None
    return abs((effect_reported - effect_reconstructed) / effect_reported)

def validate_single_record(
    summary: ABTestSummary,
    reconstruction: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single A/B test summary against its reconstruction.
    Flags inconsistencies per FR-004 and data quality issues per FR-012.

    Args:
        summary: The extracted ABTestSummary object.
        reconstruction: Dictionary containing reconstructed statistical values.

    Returns:
        AuditRecord with consistency flags and notes.
    """
    notes = []
    is_inconsistent = False
    data_quality_warning = None

    # Check for missing baseline conversion rate (FR-012)
    if summary.conversion_rate_control is None:
        notes.append("baseline conversion rate missing")
        data_quality_warning = "Missing baseline conversion rate prevents full statistical reconstruction"
        is_inconsistent = True  # Mark as inconsistent due to missing data

    # Check for missing treatment conversion rate
    if summary.conversion_rate_treatment is None:
        notes.append("treatment conversion rate missing")
        if not data_quality_warning:
            data_quality_warning = "Missing treatment conversion rate prevents full statistical reconstruction"
        is_inconsistent = True

    # Check for sample size mismatch (FR-004b)
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        if summary.sample_size_control != summary.sample_size_treatment:
            notes.append("sample size mismatch between control and treatment")
            if not data_quality_warning:
                data_quality_warning = "Sample size mismatch detected"

    # Compare p-values if both are available
    p_reported = summary.p_value_reported
    p_reconstructed = reconstruction.get("p_value_reconstructed")
    p_diff = calculate_p_value_diff(p_reported, p_reconstructed)

    if p_diff is not None:
        if p_diff > 0.05:  # FR-004 threshold
            notes.append(f"p-value difference exceeds threshold: {p_diff:.4f}")
            is_inconsistent = True

    # Compare effect sizes if both are available
    effect_reported = summary.effect_size_reported
    effect_reconstructed = reconstruction.get("effect_size_reconstructed")
    effect_diff = calculate_effect_size_diff(effect_reported, effect_reconstructed)
    relative_effect_diff = calculate_relative_effect_size_diff(effect_reported, effect_reconstructed)

    if effect_diff is not None and relative_effect_diff is not None:
        if relative_effect_diff > 0.05:  # FR-004 threshold: 5% relative difference
            notes.append(f"effect size relative difference exceeds threshold: {relative_effect_diff:.2%}")
            is_inconsistent = True

    # Create the audit record
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        is_inconsistent=is_inconsistent,
        notes="; ".join(notes) if notes else "All checks passed",
        data_quality_warning=data_quality_warning,
        p_value_difference=p_diff,
        effect_size_difference=effect_diff,
        relative_effect_size_difference=relative_effect_diff
    )

    return audit_record

def validate_all_records(
    summaries: List[ABTestSummary],
    reconstructions: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate a list of summaries against their reconstructions.

    Args:
        summaries: List of ABTestSummary objects.
        reconstructions: List of reconstruction dictionaries.

    Returns:
        List of AuditRecord objects.
    """
    if len(summaries) != len(reconstructions):
        raise ValueError(f"Number of summaries ({len(summaries)}) does not match number of reconstructions ({len(reconstructions)})")

    audit_records = []
    for summary, reconstruction in zip(summaries, reconstructions):
        record = validate_single_record(summary, reconstruction)
        audit_records.append(record)
        logger.info(f"Validated {summary.url}: inconsistent={record.is_inconsistent}")

    return audit_records

def main():
    """
    Main entry point for running validation on a dataset.
    Expects input data to be processed by the reconstructor first.
    """
    logger.info("Starting validation process")

    # This would typically load from files generated by the reconstructor
    # For now, we demonstrate the validation logic
    logger.info("Validation module loaded successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())