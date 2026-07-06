"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004: Validates statistical consistency using absolute p-difference
and relative effect-size thresholds.
Implements FR-004b: Excludes sample-size mismatch entries from aggregate prevalence
and flags them with data_quality_warning.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Thresholds per FR-004
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(
    reported_p: float, reconstructed_p: float
) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(reported_p - reconstructed_p)


def calculate_relative_effect_size_difference(
    reported_effect: float, reconstructed_effect: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Formula: |reported - reconstructed| / |reconstructed|
    Handles zero reconstructed effect by returning infinity.
    """
    if reconstructed_effect == 0.0:
        if reported_effect == 0.0:
            return 0.0
        return float('inf')
    return abs(reported_effect - reconstructed_effect) / abs(reconstructed_effect)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if sample sizes reported in the summary are inconsistent or missing.
    Returns True if there is a mismatch or critical missing data that prevents
    reliable statistical reconstruction.
    """
    # Check for missing sample sizes
    if summary.n_control is None or summary.n_treatment is None:
        return True

    # Check for zero or negative sample sizes
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return True

    # In a real implementation, we might check for internal consistency
    # between reported conversion rates and sample sizes if raw counts were available.
    # For now, we rely on the presence of valid positive integers.
    return False


def check_p_value_consistency(
    reported_p: float, reconstructed_p: float
) -> Tuple[bool, float]:
    """
    Check if p-values are consistent within the absolute threshold.
    Returns (is_consistent, difference).
    """
    diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
    is_consistent = diff <= ABSOLUTE_P_THRESHOLD
    return is_consistent, diff


def check_effect_size_consistency(
    reported_effect: float, reconstructed_effect: float
) -> Tuple[bool, float]:
    """
    Check if effect sizes are consistent within the relative threshold.
    Returns (is_consistent, relative_diff).
    """
    rel_diff = calculate_relative_effect_size_difference(
        reported_effect, reconstructed_effect
    )
    is_consistent = rel_diff <= RELATIVE_EFFECT_SIZE_THRESHOLD
    return is_consistent, rel_diff


def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    p_diff: float,
    is_effect_consistent: bool,
    effect_diff: float,
    has_sample_size_mismatch: bool,
    reconstructed_p: float,
    reconstructed_effect: float,
) -> AuditRecord:
    """Create an AuditRecord based on validation results."""
    notes = []

    if has_sample_size_mismatch:
        notes.append("Sample size mismatch or missing data detected.")

    if not is_p_consistent:
        notes.append(f"P-value discrepancy: {p_diff:.4f} (threshold: {ABSOLUTE_P_THRESHOLD})")

    if not is_effect_consistent:
        notes.append(
            f"Effect size discrepancy: {effect_diff:.4f} (threshold: {RELATIVE_EFFECT_SIZE_THRESHOLD})"
        )

    if not notes:
        notes.append("All statistical checks passed.")

    # Determine inconsistency status
    # An entry is inconsistent if p-value OR effect size fails, UNLESS it has a sample size mismatch.
    # Per FR-004b, sample size mismatches are flagged but excluded from prevalence.
    # We mark them as inconsistent for the audit report but flag them specifically.
    is_inconsistent = (not is_p_consistent) or (not is_effect_consistent)

    # If sample size mismatch exists, we add a specific warning and mark as inconsistent
    # so it can be filtered out later for prevalence calculations.
    if has_sample_size_mismatch:
        is_inconsistent = True
        notes.append("EXCLUDED from prevalence estimates due to sample size issues.")

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        is_p_consistent=is_p_consistent,
        p_difference=p_diff,
        is_effect_consistent=is_effect_consistent,
        effect_size_difference=effect_diff,
        reconstructed_p_value=reconstructed_p,
        reconstructed_effect_size=reconstructed_effect,
        data_quality_warning=has_sample_size_mismatch,
        notes=" | ".join(notes),
        validated_at=datetime.utcnow().isoformat(),
    )


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: float,
) -> AuditRecord:
    """
    Validate a single summary against reconstructed statistics.
    """
    has_sample_size_mismatch = detect_sample_size_mismatch(summary)

    # If sample size is invalid, we can't reliably check p-values or effect sizes
    # against the reported ones in a meaningful way for consistency, but we still
    # flag the record. We'll use placeholders for the diffs if we can't compute them,
    # but the reconstructor should have handled the math if possible.
    # If reconstruction failed (e.g. NaN), we treat it as inconsistent.

    if np.isnan(reconstructed_p) or np.isnan(reconstructed_effect):
        # Reconstruction failed, treat as inconsistent and mismatch
        return create_audit_record(
            summary,
            is_p_consistent=False,
            p_diff=float('inf'),
            is_effect_consistent=False,
            effect_diff=float('inf'),
            has_sample_size_mismatch=True,
            reconstructed_p=reconstructed_p,
            reconstructed_effect=reconstructed_effect,
        )

    is_p_consistent, p_diff = check_p_value_consistency(
        summary.reported_p_value, reconstructed_p
    )
    is_effect_consistent, effect_diff = check_effect_size_consistency(
        summary.reported_effect_size, reconstructed_effect
    )

    return create_audit_record(
        summary,
        is_p_consistent,
        p_diff,
        is_effect_consistent,
        effect_diff,
        has_sample_size_mismatch,
        reconstructed_p,
        reconstructed_effect,
    )


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]],
) -> List[AuditRecord]:
    """
    Validate a list of summaries against their reconstructed statistics.
    """
    if len(summaries) != len(reconstructed_results):
        raise ValueError(
            "Number of summaries must match number of reconstructed results."
        )

    audit_records = []
    for summary, result in zip(summaries, reconstructed_results):
        record = validate_summary(
            summary,
            result['reconstructed_p'],
            result['reconstructed_effect'],
        )
        audit_records.append(record)
        if record.data_quality_warning:
            logger.warning(
                f"Sample size mismatch for {summary.url}: {record.notes}"
            )
        elif not record.is_p_consistent or not record.is_effect_consistent:
            logger.info(
                f"Inconsistency detected for {summary.url}: {record.notes}"
            )

    return audit_records


def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter out records with sample-size mismatches for prevalence calculations.
    Per FR-004b, these are excluded from aggregate prevalence estimates.
    """
    return [r for r in audit_records if not r.data_quality_warning]


def write_audit_report(
    audit_records: List[AuditRecord], output_path: Path
) -> None:
    """Write audit records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records_data = [
        {
            "url": r.url,
            "domain": r.domain,
            "year": r.year,
            "is_inconsistent": r.is_inconsistent,
            "is_p_consistent": r.is_p_consistent,
            "p_difference": r.p_difference,
            "is_effect_consistent": r.is_effect_consistent,
            "effect_size_difference": r.effect_size_difference,
            "reconstructed_p_value": r.reconstructed_p_value,
            "reconstructed_effect_size": r.reconstructed_effect_size,
            "data_quality_warning": r.data_quality_warning,
            "notes": r.notes,
            "validated_at": r.validated_at,
        }
        for r in audit_records
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def main() -> None:
    """
    Entry point for running the validator on extracted summaries.
    Expects reconstructed results to be available from the reconstructor step.
    """
    logger.info("Starting inconsistency validation...")

    # Paths
    summaries_path = Path("data/processed/extracted_summaries.json")
    reconstructed_path = Path("data/processed/reconstructed_results.json")
    output_path = Path("output/audit_report.json")

    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return

    if not reconstructed_path.exists():
        logger.error(f"Reconstructed results file not found: {reconstructed_path}")
        return

    # Load data
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    with open(reconstructed_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)

    # Convert to objects
    summaries = [ABTestSummary(**s) for s in summaries_data]
    
    # Validate
    audit_records = validate_all_summaries(summaries, reconstructed_data)

    # Write report
    write_audit_report(audit_records, output_path)

    # Summary stats
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    warnings = sum(1 for r in audit_records if r.data_quality_warning)
    excluded_for_prevalence = warnings

    logger.info(f"Validation complete. Total: {total}, Inconsistent: {inconsistent}, Warnings: {warnings}")
    logger.info(f"Excluded from prevalence: {excluded_for_prevalence}")


if __name__ == "__main__":
    main()