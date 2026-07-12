"""
Inconsistency Validator Module

Implements FR-004 thresholds for statistical validity checking:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Also implements FR-004b: Exclusion of sample-size mismatch entries
from aggregate prevalence estimates and generation of data_quality_warning
messages.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Constants for FR-004 thresholds
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

# Error codes
ERR_P_VALUE_MISMATCH = "ERR-004"
ERR_EFFECT_SIZE_MISMATCH = "ERR-005"
ERR_SAMPLE_SIZE_MISMATCH = "ERR-006"


def check_p_value_consistency(
    reported_p: float,
    reconstructed_p: float,
    threshold: float = ABSOLUTE_P_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if the absolute difference between reported and reconstructed p-values
    exceeds the threshold.

    Args:
        reported_p: The p-value reported in the source summary.
        reconstructed_p: The p-value reconstructed from raw data.
        threshold: The absolute difference threshold (default 0.05).

    Returns:
        Tuple of (is_consistent, absolute_difference).
    """
    if reported_p is None or reconstructed_p is None:
        return True, 0.0  # Cannot validate if missing

    diff = abs(reported_p - reconstructed_p)
    return diff <= threshold, diff


def check_effect_size_consistency(
    reported_effect: float,
    reconstructed_effect: float,
    threshold: float = RELATIVE_EFFECT_SIZE_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if the relative difference between reported and reconstructed
    effect sizes exceeds the threshold.

    Args:
        reported_effect: The effect size reported in the source summary.
        reconstructed_effect: The effect size reconstructed from raw data.
        threshold: The relative difference threshold (default 0.05).

    Returns:
        Tuple of (is_consistent, relative_difference).
    """
    if reported_effect is None or reconstructed_effect is None:
        return True, 0.0  # Cannot validate if missing

    # Avoid division by zero
    if abs(reported_effect) < 1e-9:
        # If reported is effectively zero, check absolute difference
        if abs(reconstructed_effect) > 1e-9:
            return False, 1.0  # Max relative diff
        return True, 0.0

    rel_diff = abs(reported_effect - reconstructed_effect) / abs(reported_effect)
    return rel_diff <= threshold, rel_diff


def check_sample_size_consistency(
    reported_n_control: Optional[int],
    reported_n_treatment: Optional[int],
    reconstructed_n_control: Optional[int],
    reconstructed_n_treatment: Optional[int]
) -> Tuple[bool, str]:
    """
    Check for sample size mismatches between reported and reconstructed values.

    Args:
        reported_n_control: Reported control group size.
        reported_n_treatment: Reported treatment group size.
        reconstructed_n_control: Reconstructed control group size.
        reconstructed_n_treatment: Reconstructed treatment group size.

    Returns:
        Tuple of (is_consistent, warning_message).
    """
    # If either side has missing data, we cannot verify consistency
    if (reported_n_control is None or reported_n_treatment is None or
        reconstructed_n_control is None or reconstructed_n_treatment is None):
        return True, ""

    # Check for mismatches
    n_control_match = reported_n_control == reconstructed_n_control
    n_treatment_match = reported_n_treatment == reconstructed_n_treatment

    if not n_control_match or not n_treatment_match:
        msg = (
            f"Sample size mismatch detected. "
            f"Reported: n_control={reported_n_control}, n_treatment={reported_n_treatment}; "
            f"Reconstructed: n_control={reconstructed_n_control}, n_treatment={reconstructed_n_treatment}"
        )
        return False, msg

    return True, ""


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_stats: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single ABTestSummary against reconstructed statistics.

    Args:
        summary: The extracted ABTestSummary object.
        reconstructed_stats: Dictionary containing reconstructed statistics:
            - 'p_value': float
            - 'effect_size': float
            - 'n_control': int
            - 'n_treatment': int
            - 'test_type': str

    Returns:
        An AuditRecord with validation results and any warnings.
    """
    logger = get_default_logger()
    warnings: List[str] = []
    inconsistencies: List[Dict[str, Any]] = []
    is_consistent = True

    # Check p-value consistency
    p_consistent, p_diff = check_p_value_consistency(
        summary.reported_p_value,
        reconstructed_stats.get('p_value')
    )
    if not p_consistent:
        is_consistent = False
        msg = (
            f"P-value inconsistency: reported={summary.reported_p_value}, "
            f"reconstructed={reconstructed_stats.get('p_value')}, "
            f"difference={p_diff:.4f} (threshold={ABSOLUTE_P_THRESHOLD})"
        )
        inconsistencies.append({
            "type": "p_value_mismatch",
            "code": ERR_P_VALUE_MISMATCH,
            "message": msg,
            "reported_value": summary.reported_p_value,
            "reconstructed_value": reconstructed_stats.get('p_value'),
            "difference": p_diff
        })
        logger.warning(msg)

    # Check effect size consistency
    effect_consistent, effect_diff = check_effect_size_consistency(
        summary.reported_effect_size,
        reconstructed_stats.get('effect_size')
    )
    if not effect_consistent:
        is_consistent = False
        msg = (
            f"Effect size inconsistency: reported={summary.reported_effect_size}, "
            f"reconstructed={reconstructed_stats.get('effect_size')}, "
            f"relative_diff={effect_diff:.4f} (threshold={RELATIVE_EFFECT_SIZE_THRESHOLD})"
        )
        inconsistencies.append({
            "type": "effect_size_mismatch",
            "code": ERR_EFFECT_SIZE_MISMATCH,
            "message": msg,
            "reported_value": summary.reported_effect_size,
            "reconstructed_value": reconstructed_stats.get('effect_size'),
            "difference": effect_diff
        })
        logger.warning(msg)

    # Check sample size consistency (FR-004b)
    sample_consistent, sample_warning = check_sample_size_consistency(
        summary.n_control,
        summary.n_treatment,
        reconstructed_stats.get('n_control'),
        reconstructed_stats.get('n_treatment')
    )
    if not sample_consistent:
        # Per FR-004b, this generates a data_quality_warning
        # and the entry should be excluded from aggregate prevalence estimates
        warnings.append(sample_warning)
        inconsistencies.append({
            "type": "sample_size_mismatch",
            "code": ERR_SAMPLE_SIZE_MISMATCH,
            "message": sample_warning,
            "reported_n_control": summary.n_control,
            "reported_n_treatment": summary.n_treatment,
            "reconstructed_n_control": reconstructed_stats.get('n_control'),
            "reconstructed_n_treatment": reconstructed_stats.get('n_treatment')
        })
        logger.warning(sample_warning)

    # Construct the AuditRecord
    record = AuditRecord(
        source_url=summary.source_url,
        domain=summary.domain,
        test_type=reconstructed_stats.get('test_type', 'unknown'),
        is_consistent=is_consistent,
        inconsistencies=inconsistencies,
        data_quality_warnings=warnings if warnings else None,
        validated_at=datetime.utcnow().isoformat() + "Z"
    )

    return record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_stats_list: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate a list of summaries against their corresponding reconstructed statistics.

    Args:
        summaries: List of ABTestSummary objects.
        reconstructed_stats_list: List of dictionaries with reconstructed stats.

    Returns:
        List of AuditRecord objects.
    """
    if len(summaries) != len(reconstructed_stats_list):
        raise ValueError(
            f"Mismatch in input lengths: {len(summaries)} summaries vs "
            f"{len(reconstructed_stats_list)} reconstructed stats"
        )

    records = []
    for summary, stats in zip(summaries, reconstructed_stats_list):
        record = validate_single_summary(summary, stats)
        records.append(record)

    return records


def write_audit_report(
    records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write the audit records to a JSON file.

    Args:
        records: List of AuditRecord objects.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert AuditRecords to dictionaries
    data = []
    for record in records:
        data.append({
            "source_url": record.source_url,
            "domain": record.domain,
            "test_type": record.test_type,
            "is_consistent": record.is_consistent,
            "inconsistencies": record.inconsistencies,
            "data_quality_warnings": record.data_quality_warnings,
            "validated_at": record.validated_at
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logging.info(f"Audit report written to {output_path}")


def get_excluded_records_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter records to exclude those with sample-size mismatches for
    aggregate prevalence estimation (FR-004b).

    Args:
        records: List of AuditRecord objects.

    Returns:
        List of AuditRecord objects that do NOT have sample-size mismatches.
    """
    return [
        r for r in records
        if not any(
            inc.get('type') == 'sample_size_mismatch'
            for inc in r.inconsistencies
        )
    ]


def run_validator(
    summaries_path: Path,
    reconstructed_stats_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Main entry point to run the validator.

    Args:
        summaries_path: Path to the JSON file containing ABTestSummary objects.
        reconstructed_stats_path: Path to the JSON file containing reconstructed stats.
        output_path: Path to write the audit report.

    Returns:
        List of AuditRecord objects.
    """
    logger = get_default_logger()

    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in summaries_data]

    # Load reconstructed stats
    with open(reconstructed_stats_path, 'r', encoding='utf-8') as f:
        reconstructed_stats_list = json.load(f)

    # Validate
    records = validate_all_summaries(summaries, reconstructed_stats_list)

    # Write report
    write_audit_report(records, output_path)

    # Log summary
    total = len(records)
    inconsistent = sum(1 for r in records if not r.is_consistent)
    with_warnings = sum(1 for r in records if r.data_quality_warnings)
    excluded = len(get_excluded_records_for_prevalence(records))

    logger.info(
        f"Validation complete: {total} records, "
        f"{inconsistent} inconsistent, {with_warnings} with warnings, "
        f"{excluded} excluded from prevalence estimates"
    )

    return records


def main() -> None:
    """
    CLI entry point for the validator.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate A/B test summaries against reconstructed statistics")
    parser.add_argument(
        "--summaries",
        type=Path,
        required=True,
        help="Path to JSON file containing ABTestSummary objects"
    )
    parser.add_argument(
        "--reconstructed",
        type=Path,
        required=True,
        help="Path to JSON file containing reconstructed statistics"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the audit report JSON"
    )

    args = parser.parse_args()

    run_validator(args.summaries, args.reconstructed, args.output)


if __name__ == "__main__":
    main()
