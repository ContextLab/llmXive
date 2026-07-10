"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004: Validates statistical consistency of reconstructed tests against
reported values using defined thresholds.
Implements FR-004b: Excludes sample-size mismatch entries from aggregate prevalence estimates.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05  # Absolute difference threshold
EFFECT_SIZE_THRESHOLD = 0.05  # Relative difference threshold (5%)

def compute_relative_difference(value1: float, value2: float) -> float:
    """
    Compute relative difference between two values.
    Handles zero values gracefully.
    """
    if value1 == 0 and value2 == 0:
        return 0.0
    if value1 == 0 or value2 == 0:
        return 1.0  # Maximum difference if one is zero and other is not
    
    # Use the larger absolute value as the reference
    reference = max(abs(value1), abs(value2))
    return abs(value1 - value2) / reference

def check_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check if sample sizes are consistent within the summary.
    
    Returns:
        Tuple of (is_consistent, error_message)
    """
    if summary.sample_size_treatment is None or summary.sample_size_control is None:
        return True, None  # Missing data is handled elsewhere
    
    # Check for extreme mismatches that would invalidate statistical tests
    # For example, if one sample is 10x the other, results may be unreliable
    ratio = max(summary.sample_size_treatment, summary.sample_size_control) / max(
        min(summary.sample_size_treatment, summary.sample_size_control), 1
    )
    
    if ratio > 10:  # More than 10x difference is suspicious
        return False, f"Extreme sample size mismatch: ratio {ratio:.1f}x exceeds threshold"
    
    return True, None

def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_p_value: float,
    reconstructed_effect_size: Optional[float] = None,
    reported_p_value: Optional[float] = None,
    reported_effect_size: Optional[float] = None
) -> AuditRecord:
    """
    Validate a single A/B test summary against reconstructed statistics.
    
    Args:
        summary: The original A/B test summary
        reconstructed_p_value: P-value from statistical reconstruction
        reconstructed_effect_size: Effect size from reconstruction (if available)
        reported_p_value: P-value reported in the summary (if available)
        reported_effect_size: Effect size reported in the summary (if available)
        
    Returns:
        AuditRecord with validation results
    """
    logger = get_default_logger()
    is_inconsistent = False
    inconsistency_reasons = []
    data_quality_warnings = []
    
    # Check for sample size consistency first (FR-004b)
    sample_size_consistent, sample_size_error = check_sample_size_consistency(summary)
    if not sample_size_consistent:
        data_quality_warnings.append(sample_size_error)
        # Note: We still create the record, but flag it for exclusion from prevalence
    
    # Check p-value consistency if both reported and reconstructed are available
    if reported_p_value is not None and reconstructed_p_value is not None:
        p_diff = abs(reported_p_value - reconstructed_p_value)
        if p_diff > P_VALUE_THRESHOLD:
            is_inconsistent = True
            inconsistency_reasons.append(
                f"P-value discrepancy: reported={reported_p_value:.4f}, "
                f"reconstructed={reconstructed_p_value:.4f}, diff={p_diff:.4f}"
            )
            logger.warning(
                f"P-value inconsistency detected for {summary.url}: {inconsistency_reasons[-1]}"
            )
    
    # Check effect size consistency if both are available
    if (reported_effect_size is not None and reconstructed_effect_size is not None 
        and reported_effect_size != 0):
        effect_diff = compute_relative_difference(reported_effect_size, reconstructed_effect_size)
        if effect_diff > EFFECT_SIZE_THRESHOLD:
            is_inconsistent = True
            inconsistency_reasons.append(
                f"Effect size discrepancy: reported={reported_effect_size:.4f}, "
                f"reconstructed={reconstructed_effect_size:.4f}, rel_diff={effect_diff:.4f}"
            )
            logger.warning(
                f"Effect size inconsistency detected for {summary.url}: {inconsistency_reasons[-1]}"
            )
    
    # Create the audit record
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        inconsistency_reasons=inconsistency_reasons,
        data_quality_warnings=data_quality_warnings,
        reported_p_value=reported_p_value,
        reconstructed_p_value=reconstructed_p_value,
        reported_effect_size=reported_effect_size,
        reconstructed_effect_size=reconstructed_effect_size,
        sample_size_treatment=summary.sample_size_treatment,
        sample_size_control=summary.sample_size_control,
        validation_timestamp="2026-06-27T19:32:53.038071Z"  # Placeholder, should be dynamic
    )
    
    return audit_record

def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructor_results: Dict[str, Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries against their reconstructed statistics.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructor_results: Dictionary mapping URL to reconstruction results
            Expected format: {url: {'p_value': float, 'effect_size': float}}
            
    Returns:
        List of AuditRecord objects
    """
    audit_records = []
    
    for summary in summaries:
        reconstruction = reconstructor_results.get(summary.url, {})
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_p_value=reconstruction.get('p_value'),
            reconstructed_effect_size=reconstruction.get('effect_size'),
            reported_p_value=summary.p_value,
            reported_effect_size=summary.effect_size
        )
        
        audit_records.append(record)
    
    return audit_records

def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches
    for prevalence estimation (FR-004b).
    
    Args:
        audit_records: List of all audit records
        
    Returns:
        Filtered list excluding records with sample-size mismatch warnings
    """
    filtered = []
    for record in audit_records:
        # Check if record has sample-size mismatch warnings
        has_sample_size_warning = any(
            'sample size' in warning.lower() for warning in record.data_quality_warnings
        )
        
        if not has_sample_size_warning:
            filtered.append(record)
        else:
            # Log the exclusion for transparency
            logger = get_default_logger()
            logger.info(
                f"Excluding {record.url} from prevalence estimates due to "
                f"sample-size mismatch: {record.data_quality_warnings}"
            )
    
    return filtered

def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write audit records to JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert AuditRecord objects to dictionaries for JSON serialization
    records_data = []
    for record in audit_records:
        record_dict = {
            'url': record.url,
            'domain': record.domain,
            'is_inconsistent': record.is_inconsistent,
            'inconsistency_reasons': record.inconsistency_reasons,
            'data_quality_warnings': record.data_quality_warnings,
            'reported_p_value': record.reported_p_value,
            'reconstructed_p_value': record.reconstructed_p_value,
            'reported_effect_size': record.reported_effect_size,
            'reconstructed_effect_size': record.reconstructed_effect_size,
            'sample_size_treatment': record.sample_size_treatment,
            'sample_size_control': record.sample_size_control,
            'validation_timestamp': record.validation_timestamp
        }
        records_data.append(record_dict)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2, default=str)
    
    logger = get_default_logger()
    logger.info(f"Audit report written to {output_path} with {len(records_data)} records")

def main() -> int:
    """
    Main entry point for validator script.
    
    Reads reconstructed results from data/reconstruction_results.json,
    validates against summaries in data/extracted_summaries.json,
    and writes audit report to output/audit_report.json.
    
    Returns:
        0 on success, 1 on error
    """
    logger = get_default_logger()
    logger.info("Starting inconsistency validation")
    
    try:
        # Load extracted summaries
        summaries_path = Path("data/extracted_summaries.json")
        if not summaries_path.exists():
            logger.error(f"Summaries file not found: {summaries_path}")
            return 1
        
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries_data = json.load(f)
        
        summaries = [ABTestSummary(**item) for item in summaries_data]
        logger.info(f"Loaded {len(summaries)} summaries")
        
        # Load reconstruction results
        reconstruction_path = Path("data/reconstruction_results.json")
        if not reconstruction_path.exists():
            logger.error(f"Reconstruction results not found: {reconstruction_path}")
            return 1
        
        with open(reconstruction_path, 'r', encoding='utf-8') as f:
            reconstructor_results = json.load(f)
        
        logger.info(f"Loaded reconstruction results for {len(reconstructor_results)} summaries")
        
        # Validate all summaries
        audit_records = validate_all_summaries(summaries, reconstructor_results)
        logger.info(f"Validated {len(audit_records)} summaries")
        
        # Count inconsistencies
        inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
        logger.info(f"Found {inconsistent_count} inconsistent summaries ({inconsistent_count/len(audit_records)*100:.1f}%)")
        
        # Write full audit report
        output_path = Path("output/audit_report.json")
        write_audit_report(audit_records, output_path)
        
        # Filter for prevalence estimation and write separate file
        filtered_records = filter_for_prevalence(audit_records)
        logger.info(f"Filtered to {len(filtered_records)} records for prevalence estimation")
        
        # Write filtered records for prevalence calculation
        filtered_path = Path("output/audit_records_for_prevalence.json")
        write_audit_report(filtered_records, filtered_path)
        
        logger.info("Validation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
