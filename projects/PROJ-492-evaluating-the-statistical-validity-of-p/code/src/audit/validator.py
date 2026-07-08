"""
Inconsistency Validator Module.

Applies FR-004 thresholds to reconstructed statistical results:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b: Excludes sample-size mismatch entries from aggregate
prevalence estimates and flags them with data_quality_warning in AuditRecord.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Thresholds per FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)

def calculate_absolute_p_difference(reconstructed_p: float, reported_p: float) -> float:
    """Calculate absolute difference between reconstructed and reported p-values."""
    return abs(reconstructed_p - reported_p)

def calculate_relative_effect_size_difference(
    reconstructed_effect: float, reported_effect: float
) -> float:
    """
    Calculate relative difference in effect size.
    Handles zero baseline cases by returning 0.0 difference if both are zero,
    or 1.0 (100%) if only one is zero.
    """
    if reported_effect == 0.0:
        if reconstructed_effect == 0.0:
            return 0.0
        return 1.0  # 100% difference if baseline is 0 but we have a value
    return abs(reconstructed_effect - reported_effect) / abs(reported_effect)

def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a significant mismatch in sample sizes that would
    invalidate statistical reconstruction.
    
    Returns True if sample sizes are missing or inconsistent.
    """
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        return True
    
    # Check for extreme discrepancies (e.g., one is 0 or negative)
    if summary.sample_size_control <= 0 or summary.sample_size_treatment <= 0:
        return True
        
    return False

def check_p_value_consistency(reconstructed_p: float, reported_p: float) -> Tuple[bool, str]:
    """
    Check if p-value difference exceeds threshold.
    Returns (is_consistent, message).
    """
    diff = calculate_absolute_p_difference(reconstructed_p, reported_p)
    if diff > P_VALUE_THRESHOLD:
        return False, f"P-value difference {diff:.4f} exceeds threshold {P_VALUE_THRESHOLD}"
    return True, f"P-value difference {diff:.4f} within threshold"

def check_effect_size_consistency(reconstructed_effect: float, reported_effect: float) -> Tuple[bool, str]:
    """
    Check if relative effect-size difference exceeds threshold.
    Returns (is_consistent, message).
    """
    diff = calculate_relative_effect_size_difference(reconstructed_effect, reported_effect)
    if diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
        return False, f"Effect size relative difference {diff:.2%} exceeds threshold {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}"
    return True, f"Effect size relative difference {diff:.2%} within threshold"

def create_audit_record(
    summary: ABTestSummary,
    reconstructed_p: float,
    reported_p: float,
    reconstructed_effect: float,
    reported_effect: float,
    p_consistent: bool,
    effect_consistent: bool,
    sample_size_mismatch: bool,
    reconstruction_success: bool
) -> AuditRecord:
    """
    Create an AuditRecord object with all validation results.
    
    If sample_size_mismatch is True, sets data_quality_warning and marks
    the record as inconsistent for prevalence calculation purposes.
    """
    notes = []
    
    if not reconstruction_success:
        notes.append("Reconstruction failed")
    elif not p_consistent:
        notes.append(check_p_value_consistency(reconstructed_p, reported_p)[1])
    elif not effect_consistent:
        notes.append(check_effect_size_consistency(reconstructed_effect, reported_effect)[1])
    else:
        notes.append("All checks passed")
        
    if sample_size_mismatch:
        notes.append("SAMPLE_SIZE_MISMATCH: Excluded from prevalence estimates per FR-004b")
        
    is_inconsistent = (
        not reconstruction_success or 
        not p_consistent or 
        not effect_consistent or 
        sample_size_mismatch
    )
    
    data_quality_warning = sample_size_mismatch or not reconstruction_success
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect,
        reconstructed_effect_size=reconstructed_effect,
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        is_inconsistent=is_inconsistent,
        inconsistency_reasons=notes,
        data_quality_warning=data_quality_warning,
        timestamp=None  # Will be set by the driver
    )

def validate_summary(summary: ABTestSummary, reconstruction_result: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single ABTestSummary against its reconstruction results.
    
    Args:
        summary: The extracted A/B test summary
        reconstruction_result: Dictionary with keys:
            - 'reconstructed_p': float
            - 'reported_p': float
            - 'reconstructed_effect': float
            - 'reported_effect': float
            - 'success': bool
            
    Returns:
        AuditRecord with validation results
    """
    reconstructed_p = reconstruction_result.get('reconstructed_p', 0.0)
    reported_p = reconstruction_result.get('reported_p', 0.0)
    reconstructed_effect = reconstruction_result.get('reconstructed_effect', 0.0)
    reported_effect = reconstruction_result.get('reported_effect', 0.0)
    reconstruction_success = reconstruction_result.get('success', False)
    
    p_consistent, _ = check_p_value_consistency(reconstructed_p, reported_p)
    effect_consistent, _ = check_effect_size_consistency(reconstructed_effect, reported_effect)
    sample_size_mismatch = detect_sample_size_mismatch(summary)
    
    return create_audit_record(
        summary=summary,
        reconstructed_p=reconstructed_p,
        reported_p=reported_p,
        reconstructed_effect=reconstructed_effect,
        reported_effect=reported_effect,
        p_consistent=p_consistent,
        effect_consistent=effect_consistent,
        sample_size_mismatch=sample_size_mismatch,
        reconstruction_success=reconstruction_success
    )

def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches
    for prevalence calculation (FR-004b).
    
    Returns list of records suitable for prevalence aggregation.
    """
    return [
        record for record in audit_records 
        if not record.data_quality_warning
    ]

def validate_all_summaries(
    summaries: List[ABTestSummary], 
    reconstructions: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries and return list of AuditRecords.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructions: List of reconstruction result dictionaries
        
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructions):
        raise ValueError(
            f"Mismatch in number of summaries ({len(summaries)}) and "
            f"reconstructions ({len(reconstructions)})"
        )
        
    audit_records = []
    for summary, recon in zip(summaries, reconstructions):
        record = validate_summary(summary, recon)
        audit_records.append(record)
        if record.data_quality_warning:
            logger.warning(
                f"Data quality warning for {summary.url}: {record.inconsistency_reasons}"
            )
            
    return audit_records

def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write audit records to JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "total_records": len(audit_records),
        "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
        "data_quality_warnings": sum(1 for r in audit_records if r.data_quality_warning),
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "reported_p_value": r.reported_p_value,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_effect_size": r.reported_effect_size,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "sample_size_control": r.sample_size_control,
                "sample_size_treatment": r.sample_size_treatment,
                "is_inconsistent": r.is_inconsistent,
                "inconsistency_reasons": r.inconsistency_reasons,
                "data_quality_warning": r.data_quality_warning
            }
            for r in audit_records
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Audit report written to {output_path}")

def main():
    """Main entry point for validator module."""
    import argparse
    from code.src.models.data_models import ABTestSummary
    from code.src.audit.reconstructor import reconstruct_all
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/processed/extracted_summaries.json"),
        help="Path to extracted summaries JSON"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to output audit report JSON"
    )
    args = parser.parse_args()
    
    # Load summaries
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
        
    with open(args.input, 'r') as f:
        summaries_data = json.load(f)
        
    summaries = [ABTestSummary(**item) for item in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")
    
    # Reconstruct statistics
    reconstructions = reconstruct_all(summaries)
    logger.info(f"Reconstructed statistics for {len(reconstructions)} summaries")
    
    # Validate
    audit_records = validate_all_summaries(summaries, reconstructions)
    logger.info(f"Generated {len(audit_records)} audit records")
    
    # Write report
    write_audit_report(audit_records, args.output)
    
    # Print summary
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    warnings = sum(1 for r in audit_records if r.data_quality_warning)
    logger.info(f"Summary: {inconsistent} inconsistent, {warnings} data quality warnings")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
