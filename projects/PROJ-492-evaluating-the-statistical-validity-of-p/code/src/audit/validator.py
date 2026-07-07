"""
Inconsistency validator for A/B test summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Exclude sample-size mismatch entries from aggregate prevalence estimates.
- Generate AuditRecord objects with data_quality_warning for sample-size discrepancies.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Thresholds from FR-004
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(reconstructed_p: float, reported_p: float) -> float:
    """Calculate absolute difference between reconstructed and reported p-values."""
    if reconstructed_p is None or reported_p is None:
        return float('inf')
    return abs(reconstructed_p - reported_p)


def calculate_relative_effect_size_difference(
    reconstructed_effect: float,
    reported_effect: float
) -> float:
    """
    Calculate relative difference in effect size.
    Returns relative difference as a fraction (e.g., 0.05 for 5%).
    Handles zero reported effect to avoid division by zero.
    """
    if reconstructed_effect is None or reported_effect is None:
        return float('inf')
    if abs(reported_effect) < 1e-9:
        # If reported effect is effectively zero, use absolute difference
        return abs(reconstructed_effect)
    return abs(reconstructed_effect - reported_effect) / abs(reported_effect)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a sample size mismatch between reported and
    reconstructed values.

    Returns True if a mismatch is detected.
    """
    if summary.reconstructed_n_control is None or summary.reconstructed_n_treatment is None:
        return False
    if summary.n_control is None or summary.n_treatment is None:
        return False

    # Allow a small tolerance for floating point comparisons
    tolerance = 1.0  # 1 unit difference allowed

    n_control_match = abs(summary.reconstructed_n_control - summary.n_control) <= tolerance
    n_treatment_match = abs(summary.reconstructed_n_treatment - summary.n_treatment) <= tolerance

    return not (n_control_match and n_treatment_match)


def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if the p-value difference exceeds the threshold.

    Returns:
        Tuple of (is_consistent, absolute_difference)
    """
    reconstructed_p = summary.reconstructed_p_value
    reported_p = summary.reported_p_value

    if reconstructed_p is None or reported_p is None:
        logger.warning(f"Missing p-value data for summary from {summary.source_url}")
        return False, float('inf')

    diff = calculate_absolute_p_difference(reconstructed_p, reported_p)
    is_consistent = diff <= ABSOLUTE_P_THRESHOLD

    return is_consistent, diff


def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if the effect size difference exceeds the threshold.

    Returns:
        Tuple of (is_consistent, relative_difference)
    """
    reconstructed_effect = summary.reconstructed_effect_size
    reported_effect = summary.reported_effect_size

    if reconstructed_effect is None or reported_effect is None:
        logger.warning(f"Missing effect size data for summary from {summary.source_url}")
        return False, float('inf')

    diff = calculate_relative_effect_size_difference(reconstructed_effect, reported_effect)
    is_consistent = diff <= RELATIVE_EFFECT_SIZE_THRESHOLD

    return is_consistent, diff


def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: float,
    effect_consistent: bool,
    effect_diff: float,
    sample_size_mismatch: bool
) -> AuditRecord:
    """
    Create an AuditRecord from a summary and validation results.

    If sample_size_mismatch is True, adds a data_quality_warning.
    """
    is_inconsistent = not p_consistent or not effect_consistent

    warnings = []
    if sample_size_mismatch:
        warnings.append(
            f"Sample size mismatch detected: reported n_control={summary.n_control}, "
            f"reconstructed n_control={summary.reconstructed_n_control}; "
            f"reported n_treatment={summary.n_treatment}, "
            f"reconstructed n_treatment={summary.reconstructed_n_treatment}"
        )

    notes = []
    if not p_consistent:
        notes.append(f"P-value difference: {p_diff:.4f} (threshold: {ABSOLUTE_P_THRESHOLD})")
    if not effect_consistent:
        notes.append(f"Effect size relative difference: {effect_diff:.4f} (threshold: {RELATIVE_EFFECT_SIZE_THRESHOLD})")

    return AuditRecord(
        source_url=summary.source_url,
        domain=summary.domain,
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        reconstructed_n_control=summary.reconstructed_n_control,
        reconstructed_n_treatment=summary.reconstructed_n_treatment,
        is_inconsistent=is_inconsistent,
        p_value_consistent=p_consistent,
        effect_size_consistent=effect_consistent,
        sample_size_mismatch=sample_size_mismatch,
        data_quality_warnings=warnings if warnings else None,
        audit_notes=notes if notes else None,
        validation_timestamp="2026-06-27T19:30:00Z"  # Placeholder, should be dynamic
    )


def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single ABTestSummary against FR-004 thresholds.

    Returns an AuditRecord with consistency flags and warnings.
    """
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)
    sample_size_mismatch = detect_sample_size_mismatch(summary)

    return create_audit_record(
        summary,
        p_consistent,
        p_diff,
        effect_consistent,
        effect_diff,
        sample_size_mismatch
    )


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Validate all summaries and return a list of AuditRecords.

    Args:
        summaries: List of ABTestSummary objects to validate.

    Returns:
        List of AuditRecord objects.
    """
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
        except Exception as e:
            logger.error(f"Error validating summary from {summary.source_url}: {e}")
            # Create a failed record
            records.append(AuditRecord(
                source_url=summary.source_url,
                domain=summary.domain,
                reported_p_value=summary.reported_p_value,
                reconstructed_p_value=summary.reconstructed_p_value,
                reported_effect_size=summary.reported_effect_size,
                reconstructed_effect_size=summary.reconstructed_effect_size,
                n_control=summary.n_control,
                n_treatment=summary.n_treatment,
                reconstructed_n_control=summary.reconstructed_n_control,
                reconstructed_n_treatment=summary.reconstructed_n_treatment,
                is_inconsistent=True,
                p_value_consistent=False,
                effect_size_consistent=False,
                sample_size_mismatch=False,
                data_quality_warnings=[f"Validation error: {str(e)}"],
                audit_notes=[f"Validation failed due to error"],
                validation_timestamp="2026-06-27T19:30:00Z"
            ))
    return records


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter out records with sample-size mismatches for prevalence calculations.

    Per FR-004b, sample-size mismatch entries are excluded from aggregate
    prevalence estimates.

    Args:
        records: List of AuditRecord objects.

    Returns:
        List of AuditRecord objects with sample_size_mismatch=False.
    """
    return [r for r in records if not r.sample_size_mismatch]


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """
    Write the audit report to a JSON file.

    Args:
        records: List of AuditRecord objects.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "generated_at": "2026-06-27T19:30:00Z",
        "total_records": len(records),
        "records": [
            {
                "source_url": r.source_url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "n_control": r.n_control,
                "n_treatment": r.n_treatment,
                "reconstructed_n_control": r.reconstructed_n_control,
                "reconstructed_n_treatment": r.reconstructed_n_treatment,
                "is_inconsistent": r.is_inconsistent,
                "p_value_consistent": r.p_value_consistent,
                "effect_size_consistent": r.effect_size_consistent,
                "sample_size_mismatch": r.sample_size_mismatch,
                "data_quality_warnings": r.data_quality_warnings,
                "audit_notes": r.audit_notes,
                "validation_timestamp": r.validation_timestamp
            }
            for r in records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def main():
    """
    Main entry point for the validator script.

    Reads reconstructed summaries from data/reconstructed_summaries.json,
    validates them, and writes the audit report to output/audit_report.json.
    """
    input_path = Path("data/reconstructed_summaries.json")
    output_path = Path("output/audit_report.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**item) for item in summaries_data]

    records = validate_all_summaries(summaries)
    write_audit_report(records, output_path)

    # Log summary statistics
    total = len(records)
    inconsistent = sum(1 for r in records if r.is_inconsistent)
    sample_mismatch = sum(1 for r in records if r.sample_size_mismatch)
    valid_for_prevalence = total - sample_mismatch

    logger.info(f"Validation complete: {total} records, {inconsistent} inconsistent, "
                f"{sample_mismatch} with sample-size mismatch, {valid_for_prevalence} valid for prevalence")


if __name__ == "__main__":
    import sys
    main()
