"""
Validator module for A/B test audit.
Implements inconsistency detection based on FR-004 thresholds and FR-004b exclusions.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_THRESHOLD = 0.05  # 5% relative difference

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(p_reported - p_reconstructed)


def calculate_relative_effect_size_difference(
    effect_reported: float, effect_reconstructed: float
) -> float:
    """
    Calculate relative difference in effect size.
    Formula: |reported - reconstructed| / |reconstructed|
    Handles zero reconstructed values safely.
    """
    if abs(effect_reconstructed) < 1e-9:
        # If reconstructed is effectively zero, use absolute difference or return max
        return float('inf') if abs(effect_reported) > 0 else 0.0
    return abs(effect_reported - effect_reconstructed) / abs(effect_reconstructed)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if sample sizes in the summary are inconsistent or missing.
    Returns True if there is a mismatch or missing data that prevents validation.
    """
    if summary.n_control is None or summary.n_treatment is None:
        return True
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return True
    # Check for extreme outliers that might indicate data entry errors
    if summary.n_control > 1e9 or summary.n_treatment > 1e9:
        return True
    return False


def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value_reconstructed is None:
        return False, float('inf')

    diff = calculate_absolute_p_difference(
        summary.p_value, summary.p_value_reconstructed
    )
    is_consistent = diff <= P_VALUE_THRESHOLD
    return is_consistent, diff


def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size_reconstructed is None:
        return False, float('inf')

    diff = calculate_relative_effect_size_difference(
        summary.effect_size, summary.effect_size_reconstructed
    )
    is_consistent = diff <= EFFECT_SIZE_THRESHOLD
    return is_consistent, diff


def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: float,
    effect_consistent: bool,
    effect_diff: float,
    has_sample_size_issue: bool,
) -> AuditRecord:
    """Create an AuditRecord from validation results."""
    is_inconsistent = not p_consistent or not effect_consistent
    notes = []

    if not p_consistent:
        notes.append(f"P-value discrepancy: {p_diff:.4f} (threshold: {P_VALUE_THRESHOLD})")
    if not effect_consistent:
        notes.append(f"Effect size discrepancy: {effect_diff:.4f} (threshold: {EFFECT_SIZE_THRESHOLD})")
    
    if has_sample_size_issue:
        notes.append("Sample size mismatch or missing data detected")
    
    # Generate data_quality_warning if sample size issues exist
    data_quality_warning = None
    if has_sample_size_issue:
        data_quality_warning = "Sample size discrepancy detected; excluded from aggregate prevalence estimates per FR-004b."

    return AuditRecord(
        id=summary.id,
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        p_value_reported=summary.p_value,
        p_value_reconstructed=summary.p_value_reconstructed,
        p_value_difference=p_diff,
        effect_size_reported=summary.effect_size,
        effect_size_reconstructed=summary.effect_size_reconstructed,
        effect_size_difference=effect_diff,
        notes="; ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single A/B test summary against statistical consistency thresholds.
    Applies FR-004 thresholds and flags sample size issues per FR-004b.
    """
    has_sample_size_issue = detect_sample_size_mismatch(summary)
    
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)

    return create_audit_record(
        summary, p_consistent, p_diff, effect_consistent, effect_diff, has_sample_size_issue
    )


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample size mismatches.
    Per FR-004b, entries flagged for sample-size mismatch must be excluded 
    from aggregate prevalence estimates.
    """
    return [
        record for record in records 
        if record.data_quality_warning is None
    ]


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate all summaries and return list of audit records."""
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
        except Exception as e:
            logger.error(f"Validation failed for summary {summary.id}: {str(e)}")
            # Create a failed record
            records.append(AuditRecord(
                id=summary.id,
                url=summary.url,
                domain=summary.domain,
                is_inconsistent=True,
                p_value_reported=summary.p_value,
                p_value_reconstructed=None,
                p_value_difference=float('inf'),
                effect_size_reported=summary.effect_size,
                effect_size_reconstructed=None,
                effect_size_difference=float('inf'),
                notes=f"Validation error: {str(e)}",
                data_quality_warning=None,
                timestamp=datetime.utcnow().isoformat() + "Z"
            ))
    return records


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write audit records to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_records": len(records),
            "inconsistent_count": sum(1 for r in records if r.is_inconsistent),
            "sample_size_excluded_count": sum(1 for r in records if r.data_quality_warning is not None)
        },
        "records": [r.model_dump() for r in records]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")


def main():
    """Main entry point for validator script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries")
    parser.add_argument(
        "--input", 
        type=Path, 
        required=True,
        help="Path to JSON file containing ABTestSummary objects"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON file"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    # Load summaries
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in data]
    
    # Validate
    records = validate_all_summaries(summaries)
    
    # Write report
    write_audit_report(records, args.output)
    
    # Log summary
    inconsistent = sum(1 for r in records if r.is_inconsistent)
    excluded = sum(1 for r in records if r.data_quality_warning is not None)
    logger.info(f"Validation complete: {inconsistent} inconsistent, {excluded} excluded from prevalence")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())