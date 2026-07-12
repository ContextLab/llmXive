"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004:
- Flags inconsistencies where absolute p-value difference > 0.05
- Flags inconsistencies where relative effect-size difference > 5%
- Implements FR-004b: Excludes sample-size mismatch entries from aggregate prevalence estimates
  and generates AuditRecord objects with data_quality_warning messages for these discrepancies.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_relative_difference(value1: float, value2: float) -> float:
    """
    Calculate relative difference between two values.
    Returns absolute relative difference: |v1 - v2| / max(|v1|, |v2|, epsilon)
    """
    if value1 == 0 and value2 == 0:
        return 0.0
    denominator = max(abs(value1), abs(value2), 1e-10)
    return abs(value1 - value2) / denominator


def validate_p_value_consistency(
    reported_p: float, reconstructed_p: float
) -> Tuple[bool, float]:
    """
    Check if absolute p-value difference exceeds threshold.
    Returns (is_consistent, absolute_difference)
    """
    abs_diff = abs(reported_p - reconstructed_p)
    is_consistent = abs_diff <= P_VALUE_THRESHOLD
    return is_consistent, abs_diff


def validate_effect_size_consistency(
    reported_effect: float, reconstructed_effect: float
) -> Tuple[bool, float]:
    """
    Check if relative effect-size difference exceeds threshold.
    Returns (is_consistent, relative_difference)
    """
    rel_diff = calculate_relative_difference(reported_effect, reconstructed_effect)
    is_consistent = rel_diff <= EFFECT_SIZE_RELATIVE_THRESHOLD
    return is_consistent, rel_diff


def check_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Check if there is a sample size mismatch that would invalidate statistical tests.
    Returns True if mismatch detected, False otherwise.
    """
    # Check for missing or conflicting sample sizes
    if summary.n_control is None or summary.n_treatment is None:
        return True
    
    # If we have reconstructed sample sizes and they differ significantly
    if summary.reconstructed_n_control is not None and summary.reconstructed_n_treatment is not None:
        if (abs(summary.n_control - summary.reconstructed_n_control) > 0 or
            abs(summary.n_treatment - summary.reconstructed_n_treatment) > 0):
            return True
    
    # Check for any explicit mismatch flag in the summary
    if hasattr(summary, 'sample_size_mismatch') and summary.sample_size_mismatch:
        return True
        
    return False


def create_audit_record(
    summary: ABTestSummary,
    is_consistent: bool,
    p_diff: float,
    effect_diff: float,
    sample_size_mismatch: bool
) -> AuditRecord:
    """
    Create an AuditRecord based on validation results.
    """
    audit_notes = []
    data_quality_warnings = []

    if sample_size_mismatch:
        data_quality_warnings.append(
            "Sample size mismatch detected: reconstructed sample sizes differ from reported values. "
            "This entry will be excluded from aggregate prevalence estimates per FR-004b."
        )
        audit_notes.append("SAMPLE_SIZE_MISMATCH")

    if not is_consistent:
        if p_diff > P_VALUE_THRESHOLD:
            audit_notes.append(f"P_VALUE_INCONSISTENT: abs_diff={p_diff:.4f} > {P_VALUE_THRESHOLD}")
        if effect_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            audit_notes.append(
                f"EFFECT_SIZE_INCONSISTENT: rel_diff={effect_diff:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}"
            )

    # Determine overall consistency status
    if sample_size_mismatch:
        # Entries with sample size mismatch are flagged but may still be recorded
        # with a warning. They are excluded from prevalence calculations.
        consistency_status = "INCONSISTENT" if audit_notes else "WARNING"
    else:
        consistency_status = "CONSISTENT" if is_consistent else "INCONSISTENT"

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        sample_size_control=summary.n_control,
        sample_size_treatment=summary.n_treatment,
        reconstructed_sample_size_control=summary.reconstructed_n_control,
        reconstructed_sample_size_treatment=summary.reconstructed_n_treatment,
        is_consistent=(consistency_status == "CONSISTENT"),
        consistency_status=consistency_status,
        audit_notes="; ".join(audit_notes) if audit_notes else None,
        data_quality_warning="; ".join(data_quality_warnings) if data_quality_warnings else None,
        validation_timestamp=datetime.utcnow().isoformat()
    )


def validate_single_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single ABTestSummary against statistical consistency criteria.
    """
    # Check for sample size mismatch first (FR-004b)
    sample_size_mismatch = check_sample_size_mismatch(summary)

    # If we don't have reconstructed values, we can't validate p-values or effect sizes
    if summary.reconstructed_p_value is None or summary.reconstructed_effect_size is None:
        record = create_audit_record(
            summary,
            is_consistent=False,
            p_diff=0.0,
            effect_diff=0.0,
            sample_size_mismatch=sample_size_mismatch
        )
        if record.data_quality_warning:
            record.data_quality_warning += " Missing reconstructed values for validation."
        else:
            record.data_quality_warning = "Missing reconstructed values for validation."
        return record

    # Validate p-value consistency
    p_consistent, p_diff = validate_p_value_consistency(
        summary.p_value, summary.reconstructed_p_value
    )

    # Validate effect size consistency
    effect_consistent, effect_diff = validate_effect_size_consistency(
        summary.effect_size, summary.reconstructed_effect_size
    )

    # Overall consistency: both must pass (unless sample size mismatch is the primary issue)
    is_consistent = p_consistent and effect_consistent and not sample_size_mismatch

    return create_audit_record(
        summary,
        is_consistent=is_consistent,
        p_diff=p_diff,
        effect_diff=effect_diff,
        sample_size_mismatch=sample_size_mismatch
    )


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Validate a batch of ABTestSummary objects.
    """
    audit_records = []
    for summary in summaries:
        record = validate_single_summary(summary)
        audit_records.append(record)
        if record.data_quality_warning:
            logger.warning(
                f"Validation warning for {record.url}: {record.data_quality_warning}"
            )
        elif not record.is_consistent:
            logger.warning(
                f"Validation failed for {record.url}: {record.audit_notes}"
            )
        else:
            logger.debug(f"Validation passed for {record.url}")

    return audit_records


def filter_for_prevalence_estimation(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample size mismatches
    from aggregate prevalence estimates (FR-004b).
    """
    filtered = [
        record for record in audit_records
        if record.data_quality_warning is None or "SAMPLE_SIZE_MISMATCH" not in record.audit_notes
    ]
    
    excluded_count = len(audit_records) - len(filtered)
    if excluded_count > 0:
        logger.info(
            f"Excluded {excluded_count} records with sample size mismatches "
            f"from prevalence estimation (FR-004b)."
        )
    
    return filtered


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "consistent_count": sum(1 for r in audit_records if r.is_consistent),
        "inconsistent_count": sum(1 for r in audit_records if not r.is_consistent),
        "records_with_warnings": sum(1 for r in audit_records if r.data_quality_warning),
        "audit_records": [
            {
                "url": r.url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "sample_size_control": r.sample_size_control,
                "sample_size_treatment": r.sample_size_treatment,
                "reconstructed_sample_size_control": r.reconstructed_sample_size_control,
                "reconstructed_sample_size_treatment": r.reconstructed_sample_size_treatment,
                "is_consistent": r.is_consistent,
                "consistency_status": r.consistency_status,
                "audit_notes": r.audit_notes,
                "data_quality_warning": r.data_quality_warning,
                "validation_timestamp": r.validation_timestamp
            }
            for r in audit_records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path}")


def run_validator(
    summaries_path: Path,
    output_path: Path
) -> Tuple[List[AuditRecord], List[AuditRecord]]:
    """
    Main validator function:
    1. Load summaries from JSON
    2. Validate each summary
    3. Write audit report
    4. Return (all_records, filtered_records_for_prevalence)
    """
    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**data) for data in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries from {summaries_path}")

    # Validate
    audit_records = validate_all_summaries(summaries)

    # Write report
    write_audit_report(audit_records, output_path)

    # Filter for prevalence estimation (exclude sample size mismatches)
    filtered_records = filter_for_prevalence_estimation(audit_records)

    return audit_records, filtered_records


def main() -> int:
    """
    CLI entry point for validator.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate A/B test summaries for statistical consistency."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/processed/extracted_summaries.json"),
        help="Path to extracted summaries JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON file"
    )

    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1

    try:
        all_records, filtered_records = run_validator(args.input, args.output)
        
        logger.info(
            f"Validation complete: "
            f"{sum(1 for r in all_records if r.is_consistent)} consistent, "
            f"{sum(1 for r in all_records if not r.is_consistent)} inconsistent, "
            f"{len(filtered_records)} included in prevalence estimation."
        )
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
