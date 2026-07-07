"""
Validator module for A/B test inconsistency detection.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED

logger = get_default_logger(__name__)

# FR-004 Thresholds
P_DIFFERENCE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    if p_reported is None or p_reconstructed is None:
        return float('nan')
    return abs(p_reported - p_reconstructed)

def calculate_relative_effect_size_difference(
    effect_reported: float,
    effect_reconstructed: float
) -> float:
    """
    Calculate relative difference between reported and reconstructed effect sizes.
    Returns NaN if either value is None or if effect_reported is 0 (to avoid division by zero).
    """
    if effect_reported is None or effect_reconstructed is None:
        return float('nan')
    if abs(effect_reported) < 1e-10:  # Avoid division by near-zero
        return float('nan')
    return abs(effect_reported - effect_reconstructed) / abs(effect_reported)

def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a sample size mismatch in the summary.
    Returns True if a mismatch is detected, False otherwise.
    """
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        return False
    
    total_n = summary.sample_size_control + summary.sample_size_treatment
    if summary.total_sample_size is None:
        return False
    
    # Allow for small rounding differences (e.g., integer vs float)
    return abs(total_n - summary.total_sample_size) > 1

def check_p_value_consistency(
    summary: ABTestSummary,
    reconstructed_p: Optional[float]
) -> Tuple[bool, Optional[float]]:
    """
    Check if the reported p-value is consistent with the reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value is None or reconstructed_p is None:
        return True, None  # Cannot check if data is missing
    
    diff = calculate_absolute_p_difference(summary.p_value, reconstructed_p)
    if np.isnan(diff):
        return True, None
    
    is_consistent = diff <= P_DIFFERENCE_THRESHOLD
    return is_consistent, diff

def check_effect_size_consistency(
    summary: ABTestSummary,
    reconstructed_effect: Optional[float]
) -> Tuple[bool, Optional[float]]:
    """
    Check if the reported effect size is consistent with the reconstructed effect size.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size is None or reconstructed_effect is None:
        return True, None  # Cannot check if data is missing
    
    diff = calculate_relative_effect_size_difference(summary.effect_size, reconstructed_effect)
    if np.isnan(diff):
        return True, None
    
    is_consistent = diff <= EFFECT_SIZE_RELATIVE_THRESHOLD
    return is_consistent, diff

def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    p_difference: Optional[float],
    is_effect_consistent: bool,
    effect_difference: Optional[float],
    has_sample_size_mismatch: bool,
    reconstructed_p: Optional[float] = None,
    reconstructed_effect: Optional[float] = None
) -> AuditRecord:
    """
    Create an AuditRecord for the given summary.
    
    Implements FR-004b:
    - If sample_size_mismatch is True, the record is flagged with data_quality_warning
    - Such records should be excluded from aggregate prevalence estimates
    """
    notes = []
    warnings = []
    
    if not is_p_consistent:
        notes.append(f"P-value discrepancy: |{summary.p_value} - {reconstructed_p}| = {p_difference:.4f} > {P_DIFFERENCE_THRESHOLD}")
    
    if not is_effect_consistent:
        notes.append(f"Effect size discrepancy: relative difference = {effect_difference:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}")
    
    if has_sample_size_mismatch:
        warning_msg = "Sample size mismatch detected between component groups and total sample size"
        notes.append(warning_msg)
        warnings.append("data_quality_warning")
        # FR-004b: Flag for exclusion from prevalence estimates
        warnings.append("excluded_from_prevalence")
    
    # Determine overall consistency
    is_inconsistent = (not is_p_consistent) or (not is_effect_consistent)
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        outcome_type=summary.outcome_type,
        is_inconsistent=is_inconsistent,
        p_value_reported=summary.p_value,
        p_value_reconstructed=reconstructed_p,
        effect_size_reported=summary.effect_size,
        effect_size_reconstructed=reconstructed_effect,
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        total_sample_size=summary.total_sample_size,
        notes="\n".join(notes) if notes else None,
        warnings=warnings if warnings else None,
        audit_timestamp=datetime.utcnow().isoformat()
    )

def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: Optional[float],
    reconstructed_effect: Optional[float]
) -> AuditRecord:
    """
    Validate a single A/B test summary against reconstructed statistics.
    
    Args:
        summary: The ABTestSummary object containing reported values
        reconstructed_p: Reconstructed p-value from statistical reconstruction
        reconstructed_effect: Reconstructed effect size from statistical reconstruction
        
    Returns:
        AuditRecord with consistency flags and warnings
    """
    is_p_consistent, p_diff = check_p_value_consistency(summary, reconstructed_p)
    is_effect_consistent, effect_diff = check_effect_size_consistency(summary, reconstructed_effect)
    has_sample_size_mismatch = detect_sample_size_mismatch(summary)
    
    return create_audit_record(
        summary=summary,
        is_p_consistent=is_p_consistent,
        p_difference=p_diff,
        is_effect_consistent=is_effect_consistent,
        effect_difference=effect_diff,
        has_sample_size_mismatch=has_sample_size_mismatch,
        reconstructed_p=reconstructed_p,
        reconstructed_effect=reconstructed_effect
    )

def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_stats: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries against their reconstructed statistics.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_stats: List of dictionaries containing reconstructed p-values and effect sizes
            Each dict should have keys: 'p_value', 'effect_size'
            
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_stats):
        raise ValueError(
            f"Mismatch in number of summaries ({len(summaries)}) and reconstructed stats ({len(reconstructed_stats)})"
        )
    
    audit_records = []
    for summary, stats in zip(summaries, reconstructed_stats):
        record = validate_summary(
            summary=summary,
            reconstructed_p=stats.get('p_value'),
            reconstructed_effect=stats.get('effect_size')
        )
        audit_records.append(record)
    
    return audit_records

def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to a JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records_dict = [record.model_dump() for record in audit_records]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_dict, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")

def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches.
    
    Implements FR-004b:
    - Excludes records flagged with "excluded_from_prevalence" warning
    - These records should not be included in aggregate prevalence estimates
    
    Args:
        audit_records: List of all AuditRecord objects
        
    Returns:
        List of AuditRecord objects that should be included in prevalence calculations
    """
    filtered = []
    excluded_count = 0
    
    for record in audit_records:
        if record.warnings and "excluded_from_prevalence" in record.warnings:
            excluded_count += 1
            logger.debug(f"Excluding record from prevalence: {record.url} (sample size mismatch)")
        else:
            filtered.append(record)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records from prevalence estimates due to sample-size mismatches")
    
    return filtered

def main():
    """
    Main entry point for the validator script.
    Reads reconstructed statistics and summaries, validates them, and writes the audit report.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate A/B test summaries for statistical consistency')
    parser.add_argument('--summaries', type=str, required=True, help='Path to reconstructed summaries JSON')
    parser.add_argument('--reconstructed', type=str, required=True, help='Path to reconstructed statistics JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output audit report JSON')
    args = parser.parse_args()
    
    # Load summaries
    with open(args.summaries, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**item) for item in summaries_data]
    
    # Load reconstructed statistics
    with open(args.reconstructed, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)
    
    # Validate
    audit_records = validate_all_summaries(summaries, reconstructed_data)
    
    # Write report
    write_audit_report(audit_records, Path(args.output))
    
    # Print summary
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    excluded = sum(1 for r in audit_records if r.warnings and "excluded_from_prevalence" in r.warnings)
    
    logger.info(f"Validation complete: {total} records processed")
    logger.info(f"Inconsistent: {inconsistent} ({100*inconsistent/total:.1f}%)")
    logger.info(f"Excluded from prevalence: {excluded}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
