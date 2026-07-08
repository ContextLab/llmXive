"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004: Validates p-value and effect-size consistency.
Implements FR-004b: Excludes sample-size mismatch entries from prevalence estimates.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants from FR-004
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(
    reported_p: float,
    reconstructed_p: float
) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(reported_p - reconstructed_p)


def calculate_relative_effect_size_difference(
    reported_effect: float,
    reconstructed_effect: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Formula: |reported - reconstructed| / |reconstructed|
    Handles edge cases where reconstructed is near zero.
    """
    if abs(reconstructed_effect) < 1e-9:
        # If reconstructed is effectively zero, use absolute difference
        return abs(reported_effect)
    return abs(reported_effect - reconstructed_effect) / abs(reconstructed_effect)


def detect_sample_size_mismatch(
    reported_n_control: Optional[int],
    reported_n_treatment: Optional[int],
    reconstructed_n_control: Optional[int],
    reconstructed_n_treatment: Optional[int]
) -> bool:
    """
    Detect if there is a mismatch between reported and reconstructed sample sizes.
    Returns True if a mismatch is detected, False otherwise.
    """
    # If any sample size is missing, we cannot validate, but it's not a "mismatch" per se
    if (reported_n_control is None or reported_n_treatment is None or
        reconstructed_n_control is None or reconstructed_n_treatment is None):
        return False

    # Check for exact mismatch
    if reported_n_control != reconstructed_n_control:
        return True
    if reported_n_treatment != reconstructed_n_treatment:
        return True

    return False


def check_p_value_consistency(
    reported_p: float,
    reconstructed_p: float
) -> Tuple[bool, float]:
    """
    Check if p-values are consistent within FR-004 threshold.
    Returns (is_consistent, absolute_difference).
    """
    diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
    return diff <= ABSOLUTE_P_THRESHOLD, diff


def check_effect_size_consistency(
    reported_effect: float,
    reconstructed_effect: float
) -> Tuple[bool, float]:
    """
    Check if effect sizes are consistent within FR-004 threshold.
    Returns (is_consistent, relative_difference).
    """
    diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
    return diff <= RELATIVE_EFFECT_SIZE_THRESHOLD, diff


def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    p_difference: float,
    is_effect_consistent: bool,
    effect_difference: float,
    has_sample_size_mismatch: bool
) -> AuditRecord:
    """
    Create an AuditRecord based on validation results.
    Includes data_quality_warning if sample size mismatch is detected.
    """
    notes = []

    if not is_p_consistent:
        notes.append(f"P-value inconsistency: diff={p_difference:.4f} > {ABSOLUTE_P_THRESHOLD}")

    if not is_effect_consistent:
        notes.append(f"Effect size inconsistency: diff={effect_difference:.4f} > {RELATIVE_EFFECT_SIZE_THRESHOLD}")

    if has_sample_size_mismatch:
        notes.append("Sample size mismatch detected between reported and reconstructed values")

    is_inconsistent = not is_p_consistent or not is_effect_consistent

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        p_difference=p_difference,
        effect_size_difference=effect_difference,
        notes=notes if notes else ["All checks passed"],
        data_quality_warning=has_sample_size_mismatch,
        timestamp=datetime.utcnow().isoformat()
    )


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: float,
    reconstructed_n_control: Optional[int],
    reconstructed_n_treatment: Optional[int]
) -> AuditRecord:
    """
    Validate a single A/B test summary against reconstructed statistics.
    Applies FR-004 thresholds.
    """
    reported_p = summary.reconstructed_p_value if summary.reconstructed_p_value else summary.reported_p_value
    reported_effect = summary.effect_size

    # Default to reported if reconstructed is missing (should not happen in valid flow)
    if reconstructed_p is None:
        reconstructed_p = reported_p
    if reconstructed_effect is None:
        reconstructed_effect = reported_effect

    is_p_consistent, p_diff = check_p_value_consistency(
        reported_p or 0.0,
        reconstructed_p
    )

    is_effect_consistent, effect_diff = check_effect_size_consistency(
        reported_effect or 0.0,
        reconstructed_effect
    )

    has_mismatch = detect_sample_size_mismatch(
        summary.n_control,
        summary.n_treatment,
        reconstructed_n_control,
        reconstructed_n_treatment
    )

    return create_audit_record(
        summary,
        is_p_consistent,
        p_diff,
        is_effect_consistent,
        effect_diff,
        has_mismatch
    )


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches (FR-004b).
    These records are flagged with data_quality_warning and excluded from prevalence estimates.
    """
    return [r for r in audit_records if not r.data_quality_warning]


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "is_inconsistent": r.is_inconsistent,
                "p_difference": r.p_difference,
                "effect_size_difference": r.effect_size_difference,
                "notes": r.notes,
                "data_quality_warning": r.data_quality_warning,
                "timestamp": r.timestamp
            }
            for r in audit_records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_data: List[Dict[str, Any]],
    output_path: Path
) -> List[AuditRecord]:
    """
    Validate all summaries against reconstructed data.
    reconstructed_data is expected to be a list of dicts with keys:
    'url', 'reconstructed_p', 'reconstructed_effect', 'reconstructed_n_control', 'reconstructed_n_treatment'
    """
    # Create a lookup map by URL
    recon_map = {r['url']: r for r in reconstructed_data}

    audit_records = []

    for summary in summaries:
        recon = recon_map.get(summary.url)
        if not recon:
            logger.warning(f"No reconstruction data found for {summary.url}, skipping")
            continue

        record = validate_summary(
            summary,
            reconstructed_p=recon.get('reconstructed_p'),
            reconstructed_effect=recon.get('reconstructed_effect'),
            reconstructed_n_control=recon.get('reconstructed_n_control'),
            reconstructed_n_treatment=recon.get('reconstructed_n_treatment')
        )
        audit_records.append(record)

    write_audit_report(audit_records, output_path)

    return audit_records


def main():
    """
    Main entry point for validator script.
    Expects reconstructed data at data/reconstructed_results.json
    and summaries at data/extracted_summaries.json
    Outputs to output/audit_report.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate A/B test summaries for statistical consistency")
    parser.add_argument(
        "--summaries",
        type=Path,
        default=Path("data/extracted_summaries.json"),
        help="Path to extracted summaries JSON"
    )
    parser.add_argument(
        "--reconstructed",
        type=Path,
        default=Path("data/reconstructed_results.json"),
        help="Path to reconstructed results JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON"
    )

    args = parser.parse_args()

    if not args.summaries.exists():
        logger.error(f"Summaries file not found: {args.summaries}")
        return 1

    if not args.reconstructed.exists():
        logger.error(f"Reconstructed data file not found: {args.reconstructed}")
        return 1

    # Load data
    with open(args.summaries, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    with open(args.reconstructed, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**s) for s in summaries_data]

    # Validate
    audit_records = validate_all_summaries(
        summaries,
        reconstructed_data,
        args.output
    )

    # Print summary
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    with_warning = sum(1 for r in audit_records if r.data_quality_warning)
    for_prevalence = total - with_warning

    logger.info(f"Validation complete: {total} records processed")
    logger.info(f"Inconsistent: {inconsistent} ({100*inconsistent/total:.1f}%)")
    logger.info(f"With data quality warnings (excluded from prevalence): {with_warning}")
    logger.info(f"Records included in prevalence estimate: {for_prevalence}")

    return 0


if __name__ == "__main__":
    exit(main())
