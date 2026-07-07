"""
Inconsistency Validator Module

Implements FR-004 and FR-004b:
- Validates p-value consistency (absolute difference > 0.05)
- Validates effect size consistency (relative difference > 5%)
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for FR-004 thresholds
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(
    reported_p: float,
    reconstructed_p: float
) -> float:
    """
    Calculate the absolute difference between reported and reconstructed p-values.

    Args:
        reported_p: The p-value reported in the summary
        reconstructed_p: The p-value reconstructed from raw metrics

    Returns:
        Absolute difference between the two p-values
    """
    if reported_p is None or reconstructed_p is None:
        return float('nan')
    return abs(reported_p - reconstructed_p)


def calculate_relative_effect_size_difference(
    reported_effect: float,
    reconstructed_effect: float
) -> float:
    """
    Calculate the relative difference between reported and reconstructed effect sizes.

    Formula: |reported - reconstructed| / |reconstructed|

    Args:
        reported_effect: The effect size reported in the summary
        reconstructed_effect: The effect size reconstructed from raw metrics

    Returns:
        Relative difference as a decimal (e.g., 0.05 for 5%)
    """
    if reported_effect is None or reconstructed_effect is None:
        return float('nan')
    if reconstructed_effect == 0:
        return float('inf') if reported_effect != 0 else 0.0
    return abs(reported_effect - reconstructed_effect) / abs(reconstructed_effect)


def detect_sample_size_mismatch(
    summary: ABTestSummary
) -> Tuple[bool, Optional[str]]:
    """
    Detect if there is a mismatch between reported sample sizes and those
    implied by the raw metrics (e.g., conversions vs conversion rates).

    Args:
        summary: The ABTestSummary object to validate

    Returns:
        Tuple of (is_mismatch, warning_message)
    """
    if summary.n_control is None or summary.n_treatment is None:
        return False, None

    # Check for binary outcomes where we have conversions and rates
    if summary.conversions_control is not None and summary.conversion_rate_control is not None:
        implied_n_control = summary.conversions_control / summary.conversion_rate_control
        if not np.isclose(implied_n_control, summary.n_control, rtol=0.01):
            msg = (
                f"Sample size mismatch: Reported n_control={summary.n_control}, "
                f"but implied by conversions/rate is {implied_n_control:.0f}"
            )
            return True, msg

    if summary.conversions_treatment is not None and summary.conversion_rate_treatment is not None:
        implied_n_treatment = summary.conversions_treatment / summary.conversion_rate_treatment
        if not np.isclose(implied_n_treatment, summary.n_treatment, rtol=0.01):
            msg = (
                f"Sample size mismatch: Reported n_treatment={summary.n_treatment}, "
                f"but implied by conversions/rate is {implied_n_treatment:.0f}"
            )
            return True, msg

    return False, None


def check_p_value_consistency(
    summary: ABTestSummary
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if the reported p-value is consistent with the reconstructed p-value.

    Args:
        summary: The ABTestSummary object to validate

    Returns:
        Tuple of (is_consistent, absolute_difference, warning_message)
    """
    if summary.reconstructed_p_value is None:
        return True, float('nan'), "Reconstructed p-value missing"

    diff = calculate_absolute_p_difference(
        summary.reported_p_value,
        summary.reconstructed_p_value
    )

    if np.isnan(diff):
        return True, diff, "Could not calculate p-value difference"

    is_consistent = diff <= P_VALUE_THRESHOLD
    msg = (
        f"P-value inconsistency: Reported={summary.reported_p_value:.4f}, "
        f"Reconstructed={summary.reconstructed_p_value:.4f}, "
        f"Difference={diff:.4f} > {P_VALUE_THRESHOLD}"
    ) if not is_consistent else None

    return is_consistent, diff, msg


def check_effect_size_consistency(
    summary: ABTestSummary
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if the reported effect size is consistent with the reconstructed effect size.

    Args:
        summary: The ABTestSummary object to validate

    Returns:
        Tuple of (is_consistent, relative_difference, warning_message)
    """
    if summary.reconstructed_effect_size is None:
        return True, float('nan'), "Reconstructed effect size missing"

    diff = calculate_relative_effect_size_difference(
        summary.reported_effect_size,
        summary.reconstructed_effect_size
    )

    if np.isnan(diff) or np.isinf(diff):
        return True, diff, "Could not calculate effect size difference"

    is_consistent = diff <= EFFECT_SIZE_RELATIVE_THRESHOLD
    msg = (
        f"Effect size inconsistency: Reported={summary.reported_effect_size:.4f}, "
        f"Reconstructed={summary.reconstructed_effect_size:.4f}, "
        f"Relative difference={diff:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}"
    ) if not is_consistent else None

    return is_consistent, diff, msg


def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: float,
    effect_consistent: bool,
    effect_diff: float,
    sample_mismatch: bool,
    sample_warning: Optional[str]
) -> AuditRecord:
    """
    Create an AuditRecord based on validation results.

    Args:
        summary: The source ABTestSummary
        p_consistent: Whether p-value is consistent
        p_diff: Absolute p-value difference
        effect_consistent: Whether effect size is consistent
        effect_diff: Relative effect size difference
        sample_mismatch: Whether sample size mismatch detected
        sample_warning: Warning message for sample mismatch

    Returns:
        AuditRecord object
    """
    is_inconsistent = not (p_consistent and effect_consistent)

    warnings = []
    if not p_consistent:
        warnings.append(f"P-value discrepancy: {p_diff:.4f}")
    if not effect_consistent:
        warnings.append(f"Effect size discrepancy: {effect_diff:.2%}")
    if sample_mismatch:
        warnings.append(f"Data quality warning: {sample_warning}")

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        is_inconsistent=is_inconsistent,
        data_quality_warning=warnings if warnings else None,
        validation_details={
            "p_value_consistent": p_consistent,
            "p_value_difference": p_diff,
            "effect_size_consistent": effect_consistent,
            "effect_size_relative_difference": effect_diff,
            "sample_size_mismatch": sample_mismatch
        }
    )


def validate_summary(
    summary: ABTestSummary
) -> AuditRecord:
    """
    Validate a single ABTestSummary against FR-004 thresholds.

    Args:
        summary: The ABTestSummary to validate

    Returns:
        AuditRecord with validation results
    """
    # Check p-value consistency
    p_consistent, p_diff, _ = check_p_value_consistency(summary)

    # Check effect size consistency
    effect_consistent, effect_diff, _ = check_effect_size_consistency(summary)

    # Check sample size mismatch (FR-004b)
    sample_mismatch, sample_warning = detect_sample_size_mismatch(summary)

    # Create the audit record
    record = create_audit_record(
        summary,
        p_consistent,
        p_diff,
        effect_consistent,
        effect_diff,
        sample_mismatch,
        sample_warning
    )

    if record.is_inconsistent:
        logger.warning(f"Inconsistency detected for {summary.url}: {record.data_quality_warning}")
    elif sample_mismatch:
        logger.info(f"Sample size mismatch flagged for {summary.url} but not counted as inconsistency")

    return record


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches
    for use in aggregate prevalence estimates (FR-004b).

    Args:
        audit_records: List of AuditRecord objects

    Returns:
        Filtered list excluding records with sample_size_mismatch
    """
    filtered = [
        record for record in audit_records
        if not record.validation_details.get("sample_size_mismatch", False)
    ]
    excluded_count = len(audit_records) - len(filtered)
    if excluded_count > 0:
        logger.info(
            f"Excluded {excluded_count} records with sample-size mismatches "
            f"from prevalence calculation"
        )
    return filtered


def validate_all_summaries(
    summaries: List[ABTestSummary]
) -> List[AuditRecord]:
    """
    Validate all summaries in a list.

    Args:
        summaries: List of ABTestSummary objects

    Returns:
        List of AuditRecord objects
    """
    records = []
    for summary in summaries:
        record = validate_summary(summary)
        records.append(record)
    return records


def write_audit_report(
    records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to a JSON file.

    Args:
        records: List of AuditRecord objects
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at": datetime.now().isoformat(),
        "thresholds": {
            "p_value_absolute_difference": P_VALUE_THRESHOLD,
            "effect_size_relative_difference": EFFECT_SIZE_RELATIVE_THRESHOLD
        },
        "summary": {
            "total_records": len(records),
            "inconsistent_count": sum(1 for r in records if r.is_inconsistent),
            "sample_mismatch_count": sum(
                1 for r in records
                if r.validation_details.get("sample_size_mismatch", False)
            )
        },
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "n_control": r.n_control,
                "n_treatment": r.n_treatment,
                "is_inconsistent": r.is_inconsistent,
                "data_quality_warning": r.data_quality_warning,
                "validation_details": r.validation_details
            }
            for r in records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


from datetime import datetime  # Moved import to top for clarity in write_audit_report


def main() -> None:
    """
    Main entry point for running the validator on extracted summaries.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate A/B test summaries")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSON file containing extracted ABTestSummary objects"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON"
    )
    args = parser.parse_args()

    logger.info(f"Loading summaries from {args.input}")

    # Load summaries
    with open(args.input, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**s) for s in summaries_data]

    # Validate
    records = validate_all_summaries(summaries)

    # Write report
    write_audit_report(records, args.output)

    # Filter for prevalence (for downstream use)
    prevalence_records = filter_for_prevalence(records)
    logger.info(
        f"Prepared {len(prevalence_records)} records for prevalence calculation "
        f"(excluded {len(records) - len(prevalence_records)} with sample mismatches)"
    )


if __name__ == "__main__":
    main()
