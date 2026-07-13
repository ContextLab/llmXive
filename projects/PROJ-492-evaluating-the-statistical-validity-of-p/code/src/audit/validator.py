"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning for discrepancies.
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
P_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_relative_effect_size_diff(
    reported_effect: Optional[float],
    reconstructed_effect: Optional[float]
) -> Optional[float]:
    """
    Calculate relative difference in effect sizes.
    Returns None if either value is missing or if reported is effectively zero.
    """
    if reported_effect is None or reconstructed_effect is None:
        return None
    
    # Avoid division by zero or near-zero
    if abs(reported_effect) < 1e-9:
        return None
        
    return abs(reported_effect - reconstructed_effect) / abs(reported_effect)


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_p_value: float,
    reconstructed_effect_size: Optional[float]
) -> Tuple[bool, List[str]]:
    """
    Validate a single summary against FR-004 thresholds.
    
    Returns:
        Tuple of (is_consistent, list of warning messages)
    """
    warnings = []
    is_consistent = True

    # Check p-value difference (FR-004)
    if summary.p_value is not None:
        p_diff = abs(summary.p_value - reconstructed_p_value)
        if p_diff > P_DIFF_THRESHOLD:
            warnings.append(
                f"P-value discrepancy: reported={summary.p_value:.4f}, "
                f"reconstructed={reconstructed_p_value:.4f}, diff={p_diff:.4f} > {P_DIFF_THRESHOLD}"
            )
            is_consistent = False

    # Check effect size relative difference (FR-004)
    if summary.effect_size is not None and reconstructed_effect_size is not None:
        rel_diff = calculate_relative_effect_size_diff(
            summary.effect_size, reconstructed_effect_size
        )
        if rel_diff is not None and rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            warnings.append(
                f"Effect size discrepancy: reported={summary.effect_size:.4f}, "
                f"reconstructed={reconstructed_effect_size:.4f}, "
                f"relative_diff={rel_diff:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}"
            )
            is_consistent = False

    return is_consistent, warnings


def validate_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check for sample size mismatches (FR-004b).
    
    Returns:
        Tuple of (is_consistent, warning_message)
    """
    if summary.sample_size_a is None or summary.sample_size_b is None:
        return True, None

    # Check for extreme mismatches that might indicate data quality issues
    # For example, if one group is significantly larger than the other without explanation
    total_n = summary.sample_size_a + summary.sample_size_b
    if total_n == 0:
        return False, "Total sample size is zero"

    # Flag if one group is more than 10x the other (heuristic for potential mismatch)
    ratio = max(summary.sample_size_a, summary.sample_size_b) / max(min(summary.sample_size_a, summary.sample_size_b), 1)
    if ratio > 10.0:
        return False, f"Extreme sample size imbalance: ratio={ratio:.2f}"

    return True, None


def create_audit_record(
    summary: ABTestSummary,
    reconstructed_p_value: float,
    reconstructed_effect_size: Optional[float],
    is_consistent: bool,
    warnings: List[str],
    sample_size_warning: Optional[str] = None
) -> AuditRecord:
    """
    Create an AuditRecord from validation results.
    """
    data_quality_warning = None
    if sample_size_warning:
        data_quality_warning = sample_size_warning
    elif warnings:
        data_quality_warning = "; ".join(warnings)

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.p_value,
        reconstructed_p_value=reconstructed_p_value,
        reported_effect_size=summary.effect_size,
        reconstructed_effect_size=reconstructed_effect_size,
        sample_size_a=summary.sample_size_a,
        sample_size_b=summary.sample_size_b,
        is_consistent=is_consistent,
        warnings=warnings,
        data_quality_warning=data_quality_warning,
        validation_timestamp=datetime.utcnow().isoformat()
    )


def run_validator(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]],
    output_path: Path
) -> List[AuditRecord]:
    """
    Run validation on all summaries and generate audit report.
    
    Args:
        summaries: List of extracted ABTestSummary objects
        reconstructed_results: List of dicts with 'p_value', 'effect_size' from reconstructor
        output_path: Path to write audit_report.json
    
    Returns:
        List of AuditRecord objects
    """
    audit_records = []
    
    if len(summaries) != len(reconstructed_results):
        logger.error(
            get_error_message("ERR-404", 
                f"Mismatch between summaries ({len(summaries)}) and reconstructed results ({len(reconstructed_results)})"
            )
        )
        raise ValueError("Summary and reconstruction counts must match")

    for summary, recon in zip(summaries, reconstructed_results):
        # Validate sample size consistency first (FR-004b)
        sample_consistent, sample_warning = validate_sample_size_consistency(summary)
        
        # Validate statistical consistency (FR-004)
        is_consistent, warnings = validate_single_summary(
            summary,
            recon.get('p_value'),
            recon.get('effect_size')
        )

        # If sample size is inconsistent, mark as inconsistent and add warning
        if not sample_consistent:
            warnings.append(f"Sample size issue: {sample_warning}")
            is_consistent = False

        record = create_audit_record(
            summary,
            recon.get('p_value'),
            recon.get('effect_size'),
            is_consistent,
            warnings,
            sample_warning if not sample_consistent else None
        )
        audit_records.append(record)

        # Log warnings
        if record.warnings:
            logger.warning(
                f"Validation warnings for {summary.url}: {'; '.join(record.warnings)}"
            )

    # Write audit report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "consistent_count": sum(1 for r in audit_records if r.is_consistent),
        "inconsistent_count": sum(1 for r in audit_records if not r.is_consistent),
        "records": [r.model_dump() for r in audit_records]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")
    logger.info(
        f"Summary: {report_data['consistent_count']} consistent, "
        f"{report_data['inconsistent_count']} inconsistent"
    )

    return audit_records


def main():
    """
    Entry point for validator script.
    Expects reconstructed results and summaries to be loaded from data files.
    """
    # Default paths - can be overridden via CLI in a full implementation
    summaries_path = Path("data/processed/extracted_summaries.json")
    reconstructions_path = Path("data/processed/reconstructed_tests.json")
    output_path = Path("output/audit_report.json")

    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return 1

    if not reconstructions_path.exists():
        logger.error(f"Reconstructions file not found: {reconstructions_path}")
        return 1

    # Load data
    with open(summaries_path, 'r') as f:
        summaries_data = json.load(f)
    
    with open(reconstructions_path, 'r') as f:
        reconstructions_data = json.load(f)

    # Convert to objects
    summaries = [ABTestSummary(**item) for item in summaries_data.get('summaries', [])]
    
    # Run validation
    try:
        records = run_validator(summaries, reconstructions_data.get('results', []), output_path)
        logger.info(f"Validation complete. {len(records)} records processed.")
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
