"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning messages for discrepancies.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for thresholds (FR-004)
P_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_REL_THRESHOLD = 0.05  # 5%

# Error codes
ERR_INCONSISTENT_P_VALUE = "ERR-004"
ERR_INCONSISTENT_EFFECT_SIZE = "ERR-005"
ERR_SAMPLE_SIZE_MISMATCH = "ERR-006"

logger = get_default_logger(__name__)


def calculate_relative_difference(val1: float, val2: float) -> float:
    """Calculate relative difference between two values."""
    if val1 == 0 and val2 == 0:
        return 0.0
    if val1 == 0:
        return float('inf') if val2 != 0 else 0.0
    return abs(val1 - val2) / abs(val1)


def validate_p_value_consistency(
    reported_p: float,
    reconstructed_p: float,
    threshold: float = P_DIFF_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if the absolute difference between reported and reconstructed p-values
    exceeds the threshold.

    Returns:
        Tuple (is_consistent, absolute_difference)
    """
    diff = abs(reported_p - reconstructed_p)
    return diff <= threshold, diff


def validate_effect_size_consistency(
    reported_effect: float,
    reconstructed_effect: float,
    threshold: float = EFFECT_SIZE_REL_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if the relative difference between reported and reconstructed effect sizes
    exceeds the threshold.

    Returns:
        Tuple (is_consistent, relative_difference)
    """
    rel_diff = calculate_relative_difference(reported_effect, reconstructed_effect)
    return rel_diff <= threshold, rel_diff


def validate_sample_sizes(
    summary: ABTestSummary
) -> Tuple[bool, Optional[str]]:
    """
    Check for sample size mismatches that would invalidate statistical reconstruction.

    Returns:
        Tuple (is_valid, warning_message)
        If invalid, warning_message describes the mismatch.
    """
    if summary.n_control is None or summary.n_treatment is None:
        return False, "Missing sample size data for control or treatment group"

    # Check for negative or zero sample sizes
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return False, f"Invalid sample sizes: control={summary.n_control}, treatment={summary.n_treatment}"

    # Check for extreme imbalance that might indicate data quality issues
    # (This is a heuristic check, not a hard rule)
    ratio = max(summary.n_control, summary.n_treatment) / min(summary.n_control, summary.n_treatment)
    if ratio > 100:
        return False, f"Extreme sample size imbalance detected (ratio={ratio:.2f})"

    return True, None


def create_audit_record(
    summary: ABTestSummary,
    is_consistent: bool,
    p_diff: Optional[float] = None,
    effect_diff: Optional[float] = None,
    sample_size_warning: Optional[str] = None,
    reconstructed_p: Optional[float] = None,
    reconstructed_effect: Optional[float] = None
) -> AuditRecord:
    """Create an AuditRecord based on validation results."""
    notes = []

    if sample_size_warning:
        notes.append(f"Sample size issue: {sample_size_warning}")

    if not is_consistent:
        if p_diff is not None and p_diff > P_DIFF_THRESHOLD:
            notes.append(f"P-value discrepancy: |{summary.p_value_reported:.4f} - {reconstructed_p:.4f}| = {p_diff:.4f} > {P_DIFF_THRESHOLD}")
        if effect_diff is not None and effect_diff > EFFECT_SIZE_REL_THRESHOLD:
            notes.append(f"Effect size discrepancy: relative diff = {effect_diff:.2%} > {EFFECT_SIZE_REL_THRESHOLD:.2%}")

    # Determine status
    if sample_size_warning:
        status = "data_quality_warning"
        error_code = ERR_SAMPLE_SIZE_MISMATCH
    elif not is_consistent:
        status = "inconsistent"
        if p_diff is not None and p_diff > P_DIFF_THRESHOLD:
            error_code = ERR_INCONSISTENT_P_VALUE
        else:
            error_code = ERR_INCONSISTENT_EFFECT_SIZE
    else:
        status = "consistent"
        error_code = None

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.p_value_reported,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=summary.effect_size_reported,
        reconstructed_effect_size=reconstructed_effect,
        status=status,
        notes="; ".join(notes) if notes else "All checks passed",
        error_code=error_code,
        timestamp=datetime.utcnow().isoformat()
    )


def run_validator(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Run the inconsistency validator on a list of summaries and their reconstructed results.

    Args:
        summaries: List of ABTestSummary objects extracted from A/B test pages.
        reconstructed_results: List of dicts with keys:
            - 'index': index into summaries list
            - 'reconstructed_p': reconstructed p-value
            - 'reconstructed_effect': reconstructed effect size
            - 'is_valid': bool indicating if reconstruction was possible

    Returns:
        List of AuditRecord objects.
    """
    audit_records = []

    # Create a lookup for reconstructed results
    recon_lookup = {r['index']: r for r in reconstructed_results}

    for i, summary in enumerate(summaries):
        if i not in recon_lookup:
            # No reconstruction result for this summary
            record = create_audit_record(
                summary=summary,
                is_consistent=False,
                sample_size_warning="No reconstruction result available"
            )
            audit_records.append(record)
            continue

        recon = recon_lookup[i]

        if not recon.get('is_valid', False):
            # Reconstruction failed (e.g., missing data)
            record = create_audit_record(
                summary=summary,
                is_consistent=False,
                sample_size_warning=recon.get('error_message', 'Reconstruction failed')
            )
            audit_records.append(record)
            continue

        reconstructed_p = recon['reconstructed_p']
        reconstructed_effect = recon['reconstructed_effect']

        # Validate sample sizes first (FR-004b)
        sample_valid, sample_warning = validate_sample_sizes(summary)

        # Check p-value consistency
        p_consistent, p_diff = validate_p_value_consistency(
            summary.p_value_reported, reconstructed_p
        )

        # Check effect size consistency
        effect_consistent, effect_diff = validate_effect_size_consistency(
            summary.effect_size_reported, reconstructed_effect
        )

        # Overall consistency: both must pass
        is_consistent = p_consistent and effect_consistent

        record = create_audit_record(
            summary=summary,
            is_consistent=is_consistent,
            p_diff=p_diff if not p_consistent else None,
            effect_diff=effect_diff if not effect_consistent else None,
            sample_size_warning=sample_warning,
            reconstructed_p=reconstructed_p,
            reconstructed_effect=reconstructed_effect
        )
        audit_records.append(record)

    return audit_records


def get_prevalence_records(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with data_quality_warning status
    (i.e., sample-size mismatches) for prevalence estimation (FR-004b).

    Returns:
        List of AuditRecord objects suitable for prevalence calculation.
    """
    return [
        record for record in audit_records
        if record.status != "data_quality_warning"
    ]


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """Write audit records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "consistent_count": sum(1 for r in audit_records if r.status == "consistent"),
        "inconsistent_count": sum(1 for r in audit_records if r.status == "inconsistent"),
        "data_quality_warning_count": sum(1 for r in audit_records if r.status == "data_quality_warning"),
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "status": r.status,
                "notes": r.notes,
                "error_code": r.error_code,
                "timestamp": r.timestamp
            }
            for r in audit_records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path}")


def main():
    """
    Main entry point for the validator.
    Reads reconstructed results and summaries, runs validation, and writes audit report.
    """
    # Paths
    summaries_path = Path("data/extracted_summaries.json")
    reconstructed_path = Path("data/reconstructed_results.json")
    output_path = Path("output/audit_report.json")

    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return 1

    if not reconstructed_path.exists():
        logger.error(f"Reconstructed results file not found: {reconstructed_path}")
        return 1

    # Load data
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    with open(reconstructed_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in summaries_data]

    # Run validation
    audit_records = run_validator(summaries, reconstructed_data)

    # Write report
    write_audit_report(audit_records, output_path)

    # Log summary
    consistent = sum(1 for r in audit_records if r.status == "consistent")
    inconsistent = sum(1 for r in audit_records if r.status == "inconsistent")
    warnings = sum(1 for r in audit_records if r.status == "data_quality_warning")

    logger.info(f"Validation complete: {consistent} consistent, {inconsistent} inconsistent, {warnings} warnings")

    return 0


if __name__ == "__main__":
    exit(main())
