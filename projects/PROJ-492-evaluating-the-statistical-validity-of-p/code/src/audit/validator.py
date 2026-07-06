"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 thresholds:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Identifies sample-size mismatches.
- Excludes flagged entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning messages.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

logger = get_default_logger(__name__)

# Thresholds per FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%


def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(p_reported - p_reconstructed)


def calculate_relative_effect_size_difference(
    effect_reported: float, effect_reconstructed: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Formula: |reported - reconstructed| / |reported|
    Handles cases where reported effect is 0 or near-zero by returning a large value.
    """
    if abs(effect_reported) < 1e-9:
        return float('inf')
    return abs(effect_reported - effect_reconstructed) / abs(effect_reported)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a mismatch between reported sample sizes and
    those implied by the reconstructed test statistics.

    For now, we check if the reported sample sizes are None or inconsistent
    with the data provided in the summary.
    """
    # If sample sizes are missing, we flag it as a mismatch for data quality
    if summary.n_control is None or summary.n_treatment is None:
        return True

    # Additional logic could be added here to cross-verify with raw data
    # if available. For this implementation, missing data is the primary flag.
    return False


def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if the reported p-value is consistent with the reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value_reported is None or summary.p_value_reconstructed is None:
        return False, float('nan')

    diff = calculate_absolute_p_difference(
        summary.p_value_reported, summary.p_value_reconstructed
    )
    return diff <= P_VALUE_THRESHOLD, diff


def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if the reported effect size is consistent with the reconstructed one.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size_reported is None or summary.effect_size_reconstructed is None:
        return False, float('nan')

    diff = calculate_relative_effect_size_difference(
        summary.effect_size_reported, summary.effect_size_reconstructed
    )
    return diff <= EFFECT_SIZE_RELATIVE_THRESHOLD, diff


def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: float,
    effect_consistent: bool,
    effect_diff: float,
    sample_size_mismatch: bool
) -> AuditRecord:
    """
    Create an AuditRecord based on validation results.
    """
    is_inconsistent = False
    notes = []

    if not p_consistent:
        is_inconsistent = True
        notes.append(
            f"P-value discrepancy: reported={summary.p_value_reported}, "
            f"reconstructed={summary.p_value_reconstructed}, diff={p_diff:.4f}"
        )

    if not effect_consistent:
        is_inconsistent = True
        notes.append(
            f"Effect size discrepancy: reported={summary.effect_size_reported}, "
            f"reconstructed={summary.effect_size_reconstructed}, rel_diff={effect_diff:.4f}"
        )

    data_quality_warning = None
    if sample_size_mismatch:
        data_quality_warning = "Sample size mismatch or missing data detected."
        notes.append(data_quality_warning)
        # If sample size is mismatched, we might still consider it inconsistent
        # if other metrics are off, but the primary flag is the warning.
        # Per FR-004b, this entry should be excluded from prevalence estimates.

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=summary.p_value_reconstructed,
        p_value_diff=p_diff,
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=summary.effect_size_reconstructed,
        effect_size_diff=effect_diff,
        sample_size_mismatch=sample_size_mismatch,
        data_quality_warning=data_quality_warning,
        notes="; ".join(notes) if notes else None,
        validated_at=datetime.utcnow().isoformat()
    )


def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single ABTestSummary against FR-004 thresholds.
    """
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)
    sample_size_mismatch = detect_sample_size_mismatch(summary)

    return create_audit_record(
        summary, p_consistent, p_diff, effect_consistent, effect_diff, sample_size_mismatch
    )


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Validate a list of ABTestSummaries.
    """
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
        except Exception as e:
            logger.error(f"Error validating summary for {summary.url}: {e}")
            # Create a record indicating failure
            record = AuditRecord(
                url=summary.url,
                domain=summary.domain,
                is_inconsistent=True,
                notes=f"Validation error: {str(e)}",
                validated_at=datetime.utcnow().isoformat()
            )
            records.append(record)
    return records


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter out records that have sample size mismatches per FR-004b.
    These records should not be included in aggregate prevalence estimates.
    """
    return [r for r in records if not r.sample_size_mismatch]


def write_audit_report(records: List[AuditRecord], output_path: str) -> None:
    """
    Write the audit records to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert AuditRecord objects to dictionaries for JSON serialization
    report_data = [
        {
            "url": r.url,
            "domain": r.domain,
            "is_inconsistent": r.is_inconsistent,
            "p_value_reported": r.p_value_reported,
            "p_value_reconstructed": r.p_value_reconstructed,
            "p_value_diff": r.p_value_diff,
            "effect_size_reported": r.effect_size_reported,
            "effect_size_reconstructed": r.effect_size_reconstructed,
            "effect_size_diff": r.effect_size_diff,
            "sample_size_mismatch": r.sample_size_mismatch,
            "data_quality_warning": r.data_quality_warning,
            "notes": r.notes,
            "validated_at": r.validated_at
        }
        for r in records
    ]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def main() -> None:
    """
    Main entry point for the validator script.
    Expects input summaries in a JSON file and writes audit report to output.
    """
    import argparse
    from code.src.audit.reconstructor import reconstruct_all
    from code.src.models.data_models import ABTestSummary

    parser = argparse.ArgumentParser(description="Validate A/B test summaries.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input JSON file containing ABTestSummary objects."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/audit_report.json",
        help="Path to output JSON file for audit report."
    )
    args = parser.parse_args()

    # Load summaries
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**data) for data in summaries_data]

    # Validate
    records = validate_all_summaries(summaries)

    # Write report
    write_audit_report(records, args.output)

    # Log summary statistics
    total = len(records)
    inconsistent = sum(1 for r in records if r.is_inconsistent)
    excluded = sum(1 for r in records if r.sample_size_mismatch)

    logger.info(f"Validation complete. Total: {total}, Inconsistent: {inconsistent}, Excluded from prevalence: {excluded}")


if __name__ == "__main__":
    main()
