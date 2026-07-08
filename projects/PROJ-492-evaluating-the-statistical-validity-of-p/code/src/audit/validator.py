"""
Inconsistency validator for A/B test summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED

# Initialize logger
logger = get_default_logger(__name__)


def calculate_absolute_p_difference(
    reported_p: float, 
    reconstructed_p: float
) -> float:
    """
    Calculate absolute difference between reported and reconstructed p-values.
    
    Args:
        reported_p: P-value reported in the summary
        reconstructed_p: P-value reconstructed from raw metrics
        
    Returns:
        Absolute difference |reported_p - reconstructed_p|
    """
    return abs(reported_p - reconstructed_p)


def calculate_relative_effect_size_difference(
    reported_effect_size: float,
    reconstructed_effect_size: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    
    Formula: |reported - reconstructed| / |reconstructed| * 100
    Returns 0.0 if reconstructed is 0 to avoid division by zero.
    
    Args:
        reported_effect_size: Effect size reported in summary
        reconstructed_effect_size: Effect size reconstructed from raw metrics
        
    Returns:
        Relative difference as a percentage
    """
    if abs(reconstructed_effect_size) < 1e-9:
        # Avoid division by zero; if both are near zero, diff is 0
        if abs(reported_effect_size) < 1e-9:
            return 0.0
        return float('inf')
    
    return abs(reported_effect_size - reconstructed_effect_size) / abs(reconstructed_effect_size) * 100.0


def detect_sample_size_mismatch(
    summary: ABTestSummary
) -> Tuple[bool, Optional[str]]:
    """
    Detect if there is a sample size mismatch in the summary.
    
    Checks for:
    - Conflicting sample sizes between control and treatment groups
    - Missing sample size data
    
    Args:
        summary: ABTestSummary object containing test metrics
        
    Returns:
        Tuple of (has_mismatch, warning_message)
    """
    warnings = []
    
    # Check for missing sample sizes
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        warnings.append("Missing sample size data")
    
    # Check for conflicting sample sizes (if both present and one is clearly anomalous)
    # This is a heuristic: if one is 0 while the other is positive, it's a mismatch
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        if summary.sample_size_control <= 0 and summary.sample_size_treatment > 0:
            warnings.append("Control group sample size is non-positive")
        elif summary.sample_size_treatment <= 0 and summary.sample_size_control > 0:
            warnings.append("Treatment group sample size is non-positive")
        elif summary.sample_size_control <= 0 and summary.sample_size_treatment <= 0:
            warnings.append("Both sample sizes are non-positive")
    
    if warnings:
        return True, "; ".join(warnings)
    
    return False, None


def check_p_value_consistency(
    summary: ABTestSummary,
    threshold: float = 0.05
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    
    Args:
        summary: ABTestSummary object
        threshold: Absolute p-difference threshold (default 0.05 per FR-004)
        
    Returns:
        Tuple of (is_consistent, difference, reason)
    """
    if summary.reconstructed_p_value is None or summary.reported_p_value is None:
        return True, 0.0, "Missing p-value data for comparison"
    
    diff = calculate_absolute_p_difference(
        summary.reported_p_value,
        summary.reconstructed_p_value
    )
    
    if diff > threshold:
        return False, diff, f"Absolute p-difference ({diff:.4f}) exceeds threshold ({threshold})"
    
    return True, diff, None


def check_effect_size_consistency(
    summary: ABTestSummary,
    threshold: float = 5.0
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    
    Args:
        summary: ABTestSummary object
        threshold: Relative effect-size difference threshold in % (default 5% per FR-004)
        
    Returns:
        Tuple of (is_consistent, difference, reason)
    """
    if summary.reconstructed_effect_size is None or summary.reported_effect_size is None:
        return True, 0.0, "Missing effect size data for comparison"
    
    diff = calculate_relative_effect_size_difference(
        summary.reported_effect_size,
        summary.reconstructed_effect_size
    )
    
    if diff > threshold:
        return False, diff, f"Relative effect-size difference ({diff:.2f}%) exceeds threshold ({threshold}%)"
    
    return True, diff, None


def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_difference: float,
    effect_consistent: bool,
    effect_difference: float,
    has_sample_mismatch: bool,
    sample_mismatch_warning: Optional[str],
    is_inconsistent: bool
) -> AuditRecord:
    """
    Create an AuditRecord object from validation results.
    
    Args:
        summary: Original ABTestSummary object
        p_consistent: Whether p-value passed consistency check
        p_difference: Absolute p-difference value
        effect_consistent: Whether effect size passed consistency check
        effect_difference: Relative effect-size difference value
        has_sample_mismatch: Whether sample size mismatch was detected
        sample_mismatch_warning: Warning message for sample mismatch
        is_inconsistent: Overall inconsistency flag
        
    Returns:
        AuditRecord object with all validation metadata
    """
    notes = []
    data_quality_warnings = []
    
    if not p_consistent:
        notes.append(f"P-value inconsistency: {p_difference:.4f}")
    
    if not effect_consistent:
        notes.append(f"Effect size inconsistency: {effect_difference:.2f}%")
    
    if has_sample_mismatch:
        warning_msg = sample_mismatch_warning or "Sample size mismatch detected"
        data_quality_warnings.append(warning_msg)
        notes.append(f"Data quality warning: {warning_msg}")
    
    if is_inconsistent and not notes:
        notes.append("Inconsistent by composite criteria")
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        outcome_type=summary.outcome_type,
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        is_inconsistent=is_inconsistent,
        p_difference=p_difference,
        effect_size_difference=effect_difference,
        notes="; ".join(notes) if notes else None,
        data_quality_warnings=data_quality_warnings if data_quality_warnings else None,
        validation_timestamp=datetime.utcnow().isoformat()
    )


def validate_summary(
    summary: ABTestSummary,
    p_threshold: float = 0.05,
    effect_threshold: float = 5.0
) -> AuditRecord:
    """
    Validate a single A/B test summary against inconsistency thresholds.
    
    Args:
        summary: ABTestSummary object to validate
        p_threshold: Absolute p-difference threshold (FR-004)
        effect_threshold: Relative effect-size difference threshold in % (FR-004)
        
    Returns:
        AuditRecord with validation results
    """
    # Check sample size mismatch first
    has_mismatch, mismatch_warning = detect_sample_size_mismatch(summary)
    
    # Check p-value consistency
    p_consistent, p_diff, _ = check_p_value_consistency(summary, p_threshold)
    
    # Check effect size consistency
    effect_consistent, effect_diff, _ = check_effect_size_consistency(summary, effect_threshold)
    
    # Determine overall inconsistency
    # An entry is inconsistent if EITHER p-value OR effect size fails
    # Sample size mismatch alone does not make it "inconsistent" but adds a warning
    is_inconsistent = (not p_consistent) or (not effect_consistent)
    
    return create_audit_record(
        summary=summary,
        p_consistent=p_consistent,
        p_difference=p_diff,
        effect_consistent=effect_consistent,
        effect_difference=effect_diff,
        has_sample_mismatch=has_mismatch,
        sample_mismatch_warning=mismatch_warning,
        is_inconsistent=is_inconsistent
    )


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches
    for aggregate prevalence estimation (FR-004b).
    
    Args:
        audit_records: List of AuditRecord objects
        
    Returns:
        List of AuditRecord objects excluding those with data_quality_warnings
        related to sample-size mismatches
    """
    filtered = []
    for record in audit_records:
        if record.data_quality_warnings:
            # Check if any warning is related to sample size
            sample_warnings = [
                w for w in record.data_quality_warnings 
                if "sample" in w.lower() or "size" in w.lower()
            ]
            if sample_warnings:
                # Skip this record for prevalence calculation
                logger.info(
                    f"Excluding record from prevalence due to sample-size mismatch: {record.url}"
                )
                continue
        filtered.append(record)
    
    return filtered


def validate_all_summaries(
    summaries: List[ABTestSummary],
    p_threshold: float = 0.05,
    effect_threshold: float = 5.0
) -> List[AuditRecord]:
    """
    Validate all summaries in a list.
    
    Args:
        summaries: List of ABTestSummary objects
        p_threshold: Absolute p-difference threshold
        effect_threshold: Relative effect-size difference threshold in %
        
    Returns:
        List of AuditRecord objects
    """
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary, p_threshold, effect_threshold)
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to validate summary {summary.url}: {e}")
            # Create a minimal error record
            records.append(AuditRecord(
                url=summary.url,
                domain=summary.domain,
                outcome_type=summary.outcome_type,
                is_inconsistent=True,
                notes=f"Validation error: {str(e)}",
                validation_timestamp=datetime.utcnow().isoformat()
            ))
    
    return records


def write_audit_report(
    records: List[AuditRecord],
    output_path: str
) -> None:
    """
    Write audit records to a JSON file.
    
    Args:
        records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert AuditRecords to dicts for JSON serialization
    records_data = []
    for record in records:
        record_dict = {
            "url": record.url,
            "domain": record.domain,
            "outcome_type": record.outcome_type,
            "reported_p_value": record.reported_p_value,
            "reconstructed_p_value": record.reconstructed_p_value,
            "reported_effect_size": record.reported_effect_size,
            "reconstructed_effect_size": record.reconstructed_effect_size,
            "sample_size_control": record.sample_size_control,
            "sample_size_treatment": record.sample_size_treatment,
            "is_inconsistent": record.is_inconsistent,
            "p_difference": record.p_difference,
            "effect_size_difference": record.effect_size_difference,
            "notes": record.notes,
            "data_quality_warnings": record.data_quality_warnings,
            "validation_timestamp": record.validation_timestamp
        }
        records_data.append(record_dict)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")


def main() -> int:
    """
    Main entry point for validator script.
    
    Reads reconstructed summaries from data/reconstructed_summaries.json,
    validates them, and writes audit report to output/audit_report.json.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting inconsistency validation")
    
    # Default paths
    input_path = Path("data/reconstructed_summaries.json")
    output_path = Path("output/audit_report.json")
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    # Load summaries
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            summaries_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return 1
    
    # Convert to ABTestSummary objects
    summaries = []
    for item in summaries_data:
        try:
            summary = ABTestSummary(**item)
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Skipping invalid summary entry: {e}")
    
    if not summaries:
        logger.error("No valid summaries found in input file")
        return 1
    
    logger.info(f"Validating {len(summaries)} summaries")
    
    # Validate all summaries
    audit_records = validate_all_summaries(summaries)
    
    # Write audit report
    write_audit_report(audit_records, str(output_path))
    
    # Log summary statistics
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    with_warnings = sum(1 for r in audit_records if r.data_quality_warnings)
    
    logger.info(f"Validation complete: {inconsistent}/{total} inconsistent, {with_warnings} with data quality warnings")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
