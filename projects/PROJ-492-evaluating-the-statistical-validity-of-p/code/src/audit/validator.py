"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004: Validates statistical consistency by comparing
reported p-values against reconstructed p-values.

Thresholds:
- Absolute p-difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b: Excludes sample-size mismatch entries from
aggregate prevalence estimates and flags them with data_quality_warning.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED, set_rng_seed

# Constants for thresholds
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_relative_difference(value1: float, value2: float) -> float:
    """
    Calculate the relative difference between two values.
    Returns the absolute relative difference as a fraction (0.0 to 1.0+).
    """
    if value1 == 0 and value2 == 0:
        return 0.0
    if value1 == 0 or value2 == 0:
        return 1.0  # Infinite relative difference
    
    return abs(value1 - value2) / max(abs(value1), abs(value2))


def validate_single_summary(
    summary: ABTestSummary, 
    reconstructed_result: Dict[str, Any]
) -> Tuple[AuditRecord, bool]:
    """
    Validate a single A/B test summary against its reconstructed statistical test.
    
    Args:
        summary: The extracted A/B test summary
        reconstructed_result: The result from the reconstructor containing
                            reconstructed p-value, effect size, etc.
    
    Returns:
        Tuple of (AuditRecord, is_consistent)
    """
    warnings = []
    errors = []
    is_consistent = True
    
    reported_p = summary.reported_p_value
    reconstructed_p = reconstructed_result.get('reconstructed_p_value')
    
    reported_effect_size = summary.effect_size
    reconstructed_effect_size = reconstructed_result.get('reconstructed_effect_size')
    
    reported_n_control = summary.n_control
    reported_n_treatment = summary.n_treatment
    reconstructed_n_control = reconstructed_result.get('reconstructed_n_control')
    reconstructed_n_treatment = reconstructed_result.get('reconstructed_n_treatment')
    
    # Check for sample size mismatch (FR-004b)
    sample_size_mismatch = False
    if (reconstructed_n_control is not None and reconstructed_n_treatment is not None and
        reported_n_control is not None and reported_n_treatment is not None):
        
        # Check if reconstructed sample sizes differ from reported
        if (abs(reconstructed_n_control - reported_n_control) > 0 or
            abs(reconstructed_n_treatment - reported_n_treatment) > 0):
            sample_size_mismatch = True
            warnings.append("Sample size mismatch detected between reported and reconstructed values")
            is_consistent = False
    
    # Validate p-value consistency (FR-004)
    if reported_p is not None and reconstructed_p is not None:
        p_diff = abs(reported_p - reconstructed_p)
        if p_diff > ABSOLUTE_P_THRESHOLD:
            errors.append(f"Absolute p-value difference ({p_diff:.4f}) exceeds threshold ({ABSOLUTE_P_THRESHOLD})")
            is_consistent = False
    
    # Validate effect size consistency (FR-004)
    if reported_effect_size is not None and reconstructed_effect_size is not None:
        effect_diff_ratio = calculate_relative_difference(reported_effect_size, reconstructed_effect_size)
        if effect_diff_ratio > RELATIVE_EFFECT_SIZE_THRESHOLD:
            errors.append(f"Relative effect size difference ({effect_diff_ratio:.2%}) exceeds threshold ({RELATIVE_EFFECT_SIZE_THRESHOLD:.0%})")
            is_consistent = False
    
    # Determine overall status
    if is_consistent and not warnings and not errors:
        status = "consistent"
    elif is_consistent and warnings:
        status = "consistent_with_warnings"
    else:
        status = "inconsistent"
    
    # Create AuditRecord
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        test_type=summary.test_type,
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect_size,
        reconstructed_effect_size=reconstructed_effect_size,
        reported_n_control=reported_n_control,
        reported_n_treatment=reported_n_treatment,
        reconstructed_n_control=reconstructed_n_control,
        reconstructed_n_treatment=reconstructed_n_treatment,
        is_consistent=is_consistent,
        status=status,
        data_quality_warning=len(warnings) > 0,
        warnings=warnings if warnings else None,
        errors=errors if errors else None,
        validation_timestamp=datetime.utcnow().isoformat(),
        sample_size_mismatch=sample_size_mismatch if sample_size_mismatch else None
    )
    
    return audit_record, is_consistent


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all A/B test summaries against their reconstructed results.
    
    Args:
        summaries: List of extracted A/B test summaries
        reconstructed_results: List of reconstruction results (one per summary)
    
    Returns:
        List of AuditRecord objects
    """
    audit_records = []
    
    if len(summaries) != len(reconstructed_results):
        logger.error(f"Mismatch in number of summaries ({len(summaries)}) and reconstructed results ({len(reconstructed_results)})")
        raise ValueError("Number of summaries must match number of reconstructed results")
    
    for i, (summary, recon_result) in enumerate(zip(summaries, reconstructed_results)):
        try:
            record, _ = validate_single_summary(summary, recon_result)
            audit_records.append(record)
            
            if record.data_quality_warning:
                logger.warning(f"Data quality warning for {summary.url}: {record.warnings}")
            if record.errors:
                logger.error(f"Validation errors for {summary.url}: {record.errors}")
                
        except Exception as e:
            logger.error(f"Error validating summary {i} ({summary.url}): {e}")
            # Create a failed record
            audit_record = AuditRecord(
                url=summary.url,
                domain=summary.domain,
                test_type=summary.test_type,
                reported_p_value=summary.reported_p_value,
                reconstructed_p_value=None,
                reported_effect_size=summary.effect_size,
                reconstructed_effect_size=None,
                reported_n_control=summary.n_control,
                reported_n_treatment=summary.n_treatment,
                reconstructed_n_control=None,
                reconstructed_n_treatment=None,
                is_consistent=False,
                status="error",
                data_quality_warning=True,
                warnings=[f"Validation failed: {str(e)}"],
                errors=[f"Validation failed: {str(e)}"],
                validation_timestamp=datetime.utcnow().isoformat()
            )
            audit_records.append(audit_record)
    
    return audit_records


def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write audit records to a JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to write the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records_dict = [record.model_dump() for record in audit_records]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_dict, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path} with {len(audit_records)} records")


def run_validator(
    summaries_path: Path,
    reconstructed_results_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Main entry point for running the validator.
    
    Args:
        summaries_path: Path to JSON file containing ABTestSummary objects
        reconstructed_results_path: Path to JSON file containing reconstruction results
        output_path: Path to write the audit report
    
    Returns:
        List of AuditRecord objects
    """
    set_rng_seed(SEED)
    
    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**item) for item in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries from {summaries_path}")
    
    # Load reconstructed results
    with open(reconstructed_results_path, 'r', encoding='utf-8') as f:
        reconstructed_results = json.load(f)
    
    logger.info(f"Loaded {len(reconstructed_results)} reconstructed results from {reconstructed_results_path}")
    
    # Validate
    audit_records = validate_all_summaries(summaries, reconstructed_results)
    
    # Write report
    write_audit_report(audit_records, output_path)
    
    # Log summary statistics
    total = len(audit_records)
    consistent = sum(1 for r in audit_records if r.is_consistent)
    inconsistent = sum(1 for r in audit_records if not r.is_consistent)
    warnings = sum(1 for r in audit_records if r.data_quality_warning)
    sample_size_mismatches = sum(1 for r in audit_records if r.sample_size_mismatch)
    
    logger.info(f"Validation complete: {consistent}/{total} consistent, {inconsistent} inconsistent, {warnings} with warnings, {sample_size_mismatches} sample size mismatches")
    
    return audit_records


def main() -> int:
    """
    CLI entry point for the validator.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate A/B test summaries against reconstructed results')
    parser.add_argument('--summaries', type=str, required=True, help='Path to summaries JSON file')
    parser.add_argument('--reconstructed', type=str, required=True, help='Path to reconstructed results JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to output audit report JSON file')
    
    args = parser.parse_args()
    
    try:
        summaries_path = Path(args.summaries)
        reconstructed_path = Path(args.reconstructed)
        output_path = Path(args.output)
        
        if not summaries_path.exists():
            logger.error(f"Summaries file not found: {summaries_path}")
            return 1
        
        if not reconstructed_path.exists():
            logger.error(f"Reconstructed results file not found: {reconstructed_path}")
            return 1
        
        run_validator(summaries_path, reconstructed_path, output_path)
        return 0
        
    except Exception as e:
        logger.error(f"Validator failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
