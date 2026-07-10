"""
Inconsistency validator for A/B test summaries.

Applies FR-004 thresholds (absolute p-difference > 0.05, relative effect-size > 5%)
and handles FR-004b (exclude sample-size mismatch entries from aggregate prevalence).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger: AuditLogger = get_default_logger()


def calculate_relative_effect_size_diff(
    reported_effect: float, reconstructed_effect: float
) -> float:
    """
    Calculate relative difference in effect size.
    Returns absolute relative difference: |reported - reconstructed| / |reconstructed|
    """
    if reconstructed_effect == 0:
        return float('inf') if reported_effect != 0 else 0.0
    return abs(reported_effect - reconstructed_effect) / abs(reconstructed_effect)


def validate_single_summary(
    summary: ABTestSummary, reconstructed: Dict[str, Any]
) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a single summary against reconstructed statistics.

    Returns:
      Tuple of (is_consistent, flag_reason, data_quality_warning)
    """
    flags = []
    warnings = []

    # Check for sample size mismatch (FR-004b)
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        recon_control = reconstructed.get('sample_size_control')
        recon_treatment = reconstructed.get('sample_size_treatment')

        if recon_control is not None and recon_treatment is not None:
            if summary.sample_size_control != recon_control or summary.sample_size_treatment != recon_treatment:
                warnings.append("Sample size mismatch detected between reported and reconstructed data")
                # We still flag inconsistencies, but mark for exclusion from prevalence later

    # Check p-value consistency (FR-004)
    reported_p = summary.p_value
    reconstructed_p = reconstructed.get('reconstructed_p_value')

    if reported_p is not None and reconstructed_p is not None:
        p_diff = abs(reported_p - reconstructed_p)
        if p_diff > P_VALUE_THRESHOLD:
            flags.append(f"P-value discrepancy: |{reported_p:.4f} - {reconstructed_p:.4f}| = {p_diff:.4f} > {P_VALUE_THRESHOLD}")

    # Check effect size consistency (FR-004)
    reported_effect = summary.effect_size
    reconstructed_effect = reconstructed.get('reconstructed_effect_size')

    if reported_effect is not None and reconstructed_effect is not None:
        rel_diff = calculate_relative_effect_size_diff(reported_effect, reconstructed_effect)
        if rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            flags.append(f"Effect size discrepancy: relative difference {rel_diff:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}")

    is_consistent = len(flags) == 0
    flag_reason = "; ".join(flags) if flags else "Consistent"
    warning_msg = "; ".join(warnings) if warnings else None

    return is_consistent, flag_reason, warning_msg


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructions: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries and generate AuditRecord objects.

    Args:
        summaries: List of ABTestSummary objects from extraction
        reconstructions: List of reconstruction results from reconstructor

    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructions):
        raise ValueError(f"Number of summaries ({len(summaries)}) does not match reconstructions ({len(reconstructions)})")

    audit_records = []

    for summary, recon in zip(summaries, reconstructions):
        is_consistent, flag_reason, warning = validate_single_summary(summary, recon)

        # Create AuditRecord
        record = AuditRecord(
            url=summary.url,
            domain=summary.domain,
            is_consistent=is_consistent,
            inconsistency_reason=flag_reason if not is_consistent else None,
            data_quality_warning=warning,
            has_sample_size_mismatch=warning is not None and "Sample size mismatch" in warning,
            timestamp=datetime.utcnow().isoformat()
        )

        audit_records.append(record)

    return audit_records


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter out records with sample size mismatches for prevalence calculations (FR-004b).

    Args:
        audit_records: Full list of audit records

    Returns:
        Filtered list excluding records with sample size mismatches
    """
    return [
        record for record in audit_records
        if not record.has_sample_size_mismatch
    ]


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to JSON file.

    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records_data = [
        {
            "url": r.url,
            "domain": r.domain,
            "is_consistent": r.is_consistent,
            "inconsistency_reason": r.inconsistency_reason,
            "data_quality_warning": r.data_quality_warning,
            "has_sample_size_mismatch": r.has_sample_size_mismatch,
            "timestamp": r.timestamp
        }
        for r in audit_records
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def main() -> int:
    """
    Main entry point for validator script.

    Reads reconstructed summaries and original summaries, validates them,
    and writes the audit report.
    """
    try:
        # Paths
        summaries_path = Path("data/processed/extracted_summaries.json")
        reconstructions_path = Path("data/processed/reconstructed_summaries.json")
        output_path = Path("output/audit_report.json")

        if not summaries_path.exists():
            logger.error(f"Summaries file not found: {summaries_path}")
            return 1

        if not reconstructions_path.exists():
            logger.error(f"Reconstructions file not found: {reconstructions_path}")
            return 1

        # Load data
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries_data = json.load(f)

        with open(reconstructions_path, 'r', encoding='utf-8') as f:
            reconstructions_data = json.load(f)

        # Convert to ABTestSummary objects
        summaries = [ABTestSummary(**data) for data in summaries_data]

        # Validate
        audit_records = validate_all_summaries(summaries, reconstructions_data)

        # Write report
        write_audit_report(audit_records, output_path)

        # Log summary
        total = len(audit_records)
        inconsistent = sum(1 for r in audit_records if not r.is_consistent)
        with_mismatch = sum(1 for r in audit_records if r.has_sample_size_mismatch)

        logger.info(f"Validation complete: {total} records, {inconsistent} inconsistent, {with_mismatch} with sample size mismatch")

        return 0

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
