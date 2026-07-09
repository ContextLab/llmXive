"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord with data_quality_warning for sample-size discrepancies.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for thresholds
ABSOLUTE_P_DIFF_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%
SAMPLE_SIZE_MISMATCH_THRESHOLD = 0.05  # 5% difference allowed before flagging

logger: AuditLogger = get_default_logger(__name__)


def calculate_relative_effect_size_diff(
    reported_effect: float,
    reconstructed_effect: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Returns absolute relative difference.
    """
    if reported_effect == 0:
        # Avoid division by zero; if reported is 0 but reconstructed is not,
        # treat as infinite difference (will trigger flag)
        return float('inf') if reconstructed_effect != 0 else 0.0
    
    return abs(reported_effect - reconstructed_effect) / abs(reported_effect)


def check_sample_size_mismatch(
    summary: ABTestSummary
) -> Tuple[bool, str]:
    """
    Check if sample sizes match between reported and reconstructed data.
    Returns (is_mismatch, warning_message).
    """
    if summary.reconstructed_n_control is None or summary.reconstructed_n_treatment is None:
        return False, ""
    
    if summary.n_control is None or summary.n_treatment is None:
        return False, ""
    
    # Calculate relative difference
    n_control_diff = abs(summary.n_control - summary.reconstructed_n_control)
    n_control_rel = n_control_diff / summary.n_control if summary.n_control > 0 else 0.0
    
    n_treatment_diff = abs(summary.n_treatment - summary.reconstructed_n_treatment)
    n_treatment_rel = n_treatment_diff / summary.n_treatment if summary.n_treatment > 0 else 0.0
    
    max_rel_diff = max(n_control_rel, n_treatment_rel)
    
    if max_rel_diff > SAMPLE_SIZE_MISMATCH_THRESHOLD:
        msg = (
            f"Sample size mismatch detected: reported control={summary.n_control}, "
            f"reconstructed={summary.reconstructed_n_control}; reported treatment={summary.n_treatment}, "
            f"reconstructed={summary.reconstructed_n_treatment}. "
            f"Relative difference: {max_rel_diff:.2%}"
        )
        return True, msg
    
    return False, ""


def validate_single_summary(
    summary: ABTestSummary
) -> AuditRecord:
    """
    Validate a single A/B test summary against consistency thresholds.
    
    Returns an AuditRecord with:
    - is_inconsistent: True if any threshold is exceeded
    - data_quality_warning: Warning message if sample size mismatch
    - flags: List of specific flags triggered
    """
    flags = []
    data_quality_warning = None
    is_inconsistent = False
    
    # Check sample size mismatch first (FR-004b)
    has_mismatch, mismatch_msg = check_sample_size_mismatch(summary)
    if has_mismatch:
        data_quality_warning = mismatch_msg
        flags.append("sample_size_mismatch")
        # Sample size mismatch does NOT automatically make it inconsistent for prevalence,
        # but it gets flagged for quality warning
    
    # Check p-value consistency (FR-004)
    if summary.reconstructed_p_value is not None and summary.p_value is not None:
        p_diff = abs(summary.p_value - summary.reconstructed_p_value)
        if p_diff > ABSOLUTE_P_DIFF_THRESHOLD:
            is_inconsistent = True
            flags.append("p_value_mismatch")
            logger.warning(
                f"P-value mismatch for {summary.url}: reported={summary.p_value:.4f}, "
                f"reconstructed={summary.reconstructed_p_value:.4f}, diff={p_diff:.4f}"
            )
    
    # Check effect size consistency (FR-004)
    if summary.reconstructed_effect_size is not None and summary.effect_size is not None:
        rel_diff = calculate_relative_effect_size_diff(
            summary.effect_size, 
            summary.reconstructed_effect_size
        )
        if rel_diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
            is_inconsistent = True
            flags.append("effect_size_mismatch")
            logger.warning(
                f"Effect size mismatch for {summary.url}: reported={summary.effect_size:.4f}, "
                f"reconstructed={summary.reconstructed_effect_size:.4f}, rel_diff={rel_diff:.2%}"
            )
    
    # If only sample size mismatch, it's not inconsistent for prevalence purposes
    # but still flagged for quality
    if has_mismatch and not is_inconsistent:
        is_inconsistent = False  # Explicitly not inconsistent, just quality warning
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        flags=flags,
        data_quality_warning=data_quality_warning,
        reported_p_value=summary.p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        reported_n_control=summary.n_control,
        reconstructed_n_control=summary.reconstructed_n_control,
        reported_n_treatment=summary.n_treatment,
        reconstructed_n_treatment=summary.reconstructed_n_treatment,
        validation_timestamp=datetime.utcnow().isoformat()
    )


def validate_all_summaries(
    summaries: List[ABTestSummary]
) -> List[AuditRecord]:
    """
    Validate all summaries and return list of AuditRecords.
    """
    audit_records = []
    for summary in summaries:
        record = validate_single_summary(summary)
        audit_records.append(record)
    
    logger.info(f"Validated {len(audit_records)} summaries")
    return audit_records


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter out records with sample-size mismatches for prevalence estimation (FR-004b).
    
    Returns only records that should be included in aggregate prevalence calculations.
    """
    return [
        record for record in audit_records 
        if "sample_size_mismatch" not in record.flags
    ]


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(audit_records),
            "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
            "sample_size_mismatch_count": sum(1 for r in audit_records if "sample_size_mismatch" in r.flags)
        },
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "year": r.year,
                "is_inconsistent": r.is_inconsistent,
                "flags": r.flags,
                "data_quality_warning": r.data_quality_warning,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "reported_n_control": r.reported_n_control,
                "reconstructed_n_control": r.reconstructed_n_control,
                "reported_n_treatment": r.reported_n_treatment,
                "reconstructed_n_treatment": r.reconstructed_n_treatment,
                "validation_timestamp": r.validation_timestamp
            }
            for r in audit_records
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Audit report written to {output_path}")


def main() -> int:
    """
    Main entry point for validator script.
    Reads reconstructed summaries, validates them, writes audit report.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries for consistency")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/processed/reconstructed_summaries.json"),
        help="Path to reconstructed summaries JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON"
    )
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    # Load summaries
    with open(args.input, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**data) for data in summaries_data]
    
    # Validate
    audit_records = validate_all_summaries(summaries)
    
    # Write report
    write_audit_report(audit_records, args.output)
    
    # Print summary
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    mismatch_count = sum(1 for r in audit_records if "sample_size_mismatch" in r.flags)
    prevalence_eligible = len(filter_for_prevalence(audit_records))
    
    logger.info(f"Total records: {len(audit_records)}")
    logger.info(f"Inconsistent: {inconsistent_count}")
    logger.info(f"Sample size mismatches: {mismatch_count}")
    logger.info(f"Eligible for prevalence: {prevalence_eligible}")
    
    return 0


if __name__ == "__main__":
    import sys
    from datetime import datetime
    sys.exit(main())
