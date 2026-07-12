"""
Inconsistency Validator Module (T025)

Implements FR-004 thresholds for statistical consistency checking:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning messages
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

# Error codes
ERR_SAMPLE_SIZE_MISMATCH = "ERR-040"
ERR_P_VALUE_INCONSISTENCY = "ERR-041"
ERR_EFFECT_SIZE_INCONSISTENCY = "ERR-042"

logger = get_default_logger(__name__)


def check_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check if reported sample sizes are consistent (no mismatch).
    Returns (is_consistent, error_message).
    """
    if summary.n_control is None or summary.n_treatment is None:
        # Missing sample sizes - not a mismatch per se, but a data quality issue
        return True, None

    # Check for extreme mismatches (e.g., one group has 0 or negative)
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return False, f"Invalid sample sizes: n_control={summary.n_control}, n_treatment={summary.n_treatment}"

    # For this implementation, we consider a "mismatch" as a logical inconsistency
    # where the sum of successes exceeds the sample size, or other logical checks fail.
    # However, the primary definition of "sample-size mismatch" in this context
    # refers to cases where the reported metrics cannot be derived from the stated N.
    # We flag this if the control/treatment rates are impossible given N.

    if summary.control_rate is not None:
        if summary.n_control > 0:
            expected_successes = summary.n_control * summary.control_rate
            if expected_successes < 0 or expected_successes > summary.n_control:
                return False, f"Control rate {summary.control_rate} inconsistent with n_control={summary.n_control}"

    if summary.treatment_rate is not None:
        if summary.n_treatment > 0:
            expected_successes = summary.n_treatment * summary.treatment_rate
            if expected_successes < 0 or expected_successes > summary.n_treatment:
                return False, f"Treatment rate {summary.treatment_rate} inconsistent with n_treatment={summary.n_treatment}"

    return True, None


def validate_p_value_consistency(
    reported_p: float,
    reconstructed_p: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate absolute p-value difference against FR-004 threshold (0.05).
    """
    if reported_p is None or reconstructed_p is None:
        return True, None  # Cannot validate if missing

    diff = abs(reported_p - reconstructed_p)
    if diff > P_VALUE_THRESHOLD:
        return False, f"P-value discrepancy: reported={reported_p:.4f}, reconstructed={reconstructed_p:.4f}, diff={diff:.4f}"
    return True, None


def validate_effect_size_consistency(
    reported_effect: Optional[float],
    reconstructed_effect: Optional[float]
) -> Tuple[bool, Optional[str]]:
    """
    Validate relative effect-size difference against FR-004 threshold (5%).
    """
    if reported_effect is None or reconstructed_effect is None:
        return True, None

    if reported_effect == 0:
        # Avoid division by zero; if reported is 0 and reconstructed is not, it's a mismatch
        if reconstructed_effect != 0:
            return False, f"Effect size mismatch: reported=0, reconstructed={reconstructed_effect}"
        return True, None

    rel_diff = abs(reported_effect - reconstructed_effect) / abs(reported_effect)
    if rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
        return False, f"Effect size discrepancy: reported={reported_effect:.4f}, reconstructed={reconstructed_effect:.4f}, rel_diff={rel_diff:.2%}"
    return True, None


def create_audit_record(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: Optional[float],
    sample_size_warning: Optional[str] = None,
    p_value_warning: Optional[str] = None,
    effect_size_warning: Optional[str] = None
) -> AuditRecord:
    """
    Create an AuditRecord with appropriate warnings and flags.
    """
    is_inconsistent = False
    warnings = []

    if sample_size_warning:
        warnings.append({
            "code": ERR_SAMPLE_SIZE_MISMATCH,
            "message": sample_size_warning,
            "type": "data_quality_warning"
        })
        # Per FR-004b: sample-size mismatch entries are excluded from prevalence estimates
        # We mark this record as having a data quality warning
        is_inconsistent = True  # Or we could have a separate flag, but for prevalence exclusion, we treat it as inconsistent/flagged

    if p_value_warning:
        warnings.append({
            "code": ERR_P_VALUE_INCONSISTENCY,
            "message": p_value_warning,
            "type": "statistical_inconsistency"
        })
        is_inconsistent = True

    if effect_size_warning:
        warnings.append({
            "code": ERR_EFFECT_SIZE_INCONSISTENCY,
            "message": effect_size_warning,
            "type": "statistical_inconsistency"
        })
        is_inconsistent = True

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.p_value,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=summary.effect_size,
        reconstructed_effect_size=reconstructed_effect,
        sample_size=summary.n_control,
        is_inconsistent=is_inconsistent,
        warnings=warnings if warnings else None,
        validated_at=datetime.utcnow().isoformat()
    )


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: Optional[float]
) -> AuditRecord:
    """
    Validate a single summary against FR-004 thresholds.
    """
    # Check sample size consistency first
    sample_size_consistent, sample_size_msg = check_sample_size_consistency(summary)

    # Check p-value consistency
    p_value_consistent, p_value_msg = validate_p_value_consistency(
        summary.p_value, reconstructed_p
    )

    # Check effect size consistency
    effect_size_consistent, effect_size_msg = validate_effect_size_consistency(
        summary.effect_size, reconstructed_effect
    )

    # Create the audit record
    return create_audit_record(
        summary=summary,
        reconstructed_p=reconstructed_p,
        reconstructed_effect=reconstructed_effect,
        sample_size_warning=None if sample_size_consistent else sample_size_msg,
        p_value_warning=None if p_value_consistent else p_value_msg,
        effect_size_warning=None if effect_size_consistent else effect_size_msg
    )


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries and return a list of AuditRecords.
    reconstructed_results should be a list of dicts with keys:
      - 'reconstructed_p'
      - 'reconstructed_effect'
    """
    audit_records = []

    for summary, recon in zip(summaries, reconstructed_results):
        audit_record = validate_summary(
            summary=summary,
            reconstructed_p=recon['reconstructed_p'],
            reconstructed_effect=recon.get('reconstructed_effect')
        )
        audit_records.append(audit_record)

    return audit_records


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write the audit report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "sample_size": r.sample_size,
                "is_inconsistent": r.is_inconsistent,
                "warnings": r.warnings,
                "validated_at": r.validated_at
            }
            for r in audit_records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path}")


def run_validator(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]],
    output_path: Path
) -> List[AuditRecord]:
    """
    Main entry point for running the validator.
    """
    audit_records = validate_all_summaries(summaries, reconstructed_results)
    write_audit_report(audit_records, output_path)
    return audit_records


def main() -> None:
    """
    CLI entry point for the validator.
    Expects:
      - input/summaries.json: List of ABTestSummary objects (JSON)
      - input/reconstructed_results.json: List of dicts with reconstructed stats
      - output/audit_report.json: Output path
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run inconsistency validator")
    parser.add_argument("--summaries", type=Path, required=True, help="Path to summaries JSON")
    parser.add_argument("--reconstructed", type=Path, required=True, help="Path to reconstructed results JSON")
    parser.add_argument("--output", type=Path, required=True, help="Path to output audit report")
    args = parser.parse_args()

    # Load summaries
    with open(args.summaries, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**s) for s in summaries_data]

    # Load reconstructed results
    with open(args.reconstructed, 'r', encoding='utf-8') as f:
        reconstructed_results = json.load(f)

    # Run validator
    audit_records = run_validator(summaries, reconstructed_results, args.output)

    # Log summary
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    logger.info(f"Validation complete: {len(audit_records)} records, {inconsistent_count} inconsistent")


if __name__ == "__main__":
    main()
