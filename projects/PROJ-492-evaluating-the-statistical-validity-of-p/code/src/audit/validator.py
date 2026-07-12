"""
Inconsistency Validator Module

Implements FR-004 thresholds for statistical consistency checking:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Also implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies
- Writes output/audit_report.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED

# Set random seed for reproducibility
np.random.seed(SEED)

# Thresholds from FR-004
ABSOLUTE_P_DIFF_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

# Error codes
ERR_SAMPLE_SIZE_MISMATCH = "ERR-101"
ERR_P_VALUE_INCONSISTENCY = "ERR-102"
ERR_EFFECT_SIZE_INCONSISTENCY = "ERR-103"

logger = get_default_logger(__name__)


def check_sample_size_match(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check if sample sizes are consistent between control and treatment groups.
    
    Args:
        summary: The ABTestSummary object to validate
        
    Returns:
        Tuple of (is_match, error_message)
    """
    if summary.n_control is None or summary.n_treatment is None:
        return False, "Missing sample size data"
    
    # Check for reasonable sample size ranges
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return False, "Invalid sample size (must be positive)"
    
    # Check for extreme mismatches (e.g., one group is 10x larger than the other)
    # This could indicate data quality issues
    ratio = max(summary.n_control, summary.n_treatment) / min(summary.n_control, summary.n_treatment)
    if ratio > 10:
        return False, f"Extreme sample size mismatch (ratio: {ratio:.2f})"
    
    return True, None


def calculate_effect_size(summary: ABTestSummary) -> Optional[float]:
    """
    Calculate the effect size (difference in proportions or means) from the summary.
    
    Args:
        summary: The ABTestSummary object
        
    Returns:
        Effect size value or None if not calculable
    """
    if summary.is_binary:
        if summary.conversion_control is not None and summary.conversion_treatment is not None:
            return summary.conversion_treatment - summary.conversion_control
    else:
        if summary.mean_control is not None and summary.mean_treatment is not None:
            return summary.mean_treatment - summary.mean_control
    
    return None


def calculate_effect_size_baseline(summary: ABTestSummary) -> Optional[float]:
    """
    Calculate the baseline effect size (control group value) for relative comparison.
    
    Args:
        summary: The ABTestSummary object
        
    Returns:
        Baseline value or None if not calculable
    """
    if summary.is_binary:
        return summary.conversion_control
    else:
        return summary.mean_control


def validate_p_value_consistency(
    reported_p: float,
    reconstructed_p: float
) -> Tuple[bool, Optional[str]]:
    """
    Check if the reported p-value is consistent with the reconstructed p-value.
    
    Args:
        reported_p: The p-value reported in the summary
        reconstructed_p: The p-value reconstructed from the data
        
    Returns:
        Tuple of (is_consistent, error_message)
    """
    if reported_p is None or reconstructed_p is None:
        return True, None  # Cannot validate if either is missing
    
    abs_diff = abs(reported_p - reconstructed_p)
    if abs_diff > ABSOLUTE_P_DIFF_THRESHOLD:
        return False, f"P-value discrepancy: reported={reported_p:.4f}, reconstructed={reconstructed_p:.4f}, diff={abs_diff:.4f}"
    
    return True, None


def validate_effect_size_consistency(
    reported_effect: float,
    reconstructed_effect: float,
    baseline: float
) -> Tuple[bool, Optional[str]]:
    """
    Check if the reported effect size is consistent with the reconstructed effect size.
    
    Args:
        reported_effect: The effect size reported in the summary
        reconstructed_effect: The effect size reconstructed from the data
        baseline: The baseline value for relative comparison
        
    Returns:
        Tuple of (is_consistent, error_message)
    """
    if reported_effect is None or reconstructed_effect is None:
        return True, None  # Cannot validate if either is missing
    
    if baseline is None or baseline == 0:
        # Cannot calculate relative difference if baseline is zero or missing
        # Fall back to absolute comparison
        abs_diff = abs(reported_effect - reconstructed_effect)
        if abs_diff > ABSOLUTE_P_DIFF_THRESHOLD:
            return False, f"Effect size discrepancy (absolute): reported={reported_effect:.4f}, reconstructed={reconstructed_effect:.4f}"
        return True, None
    
    # Calculate relative difference
    relative_diff = abs(reported_effect - reconstructed_effect) / abs(baseline)
    if relative_diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
        return False, f"Effect size discrepancy (relative {relative_diff*100:.1f}%): reported={reported_effect:.4f}, reconstructed={reconstructed_effect:.4f}, baseline={baseline:.4f}"
    
    return True, None


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: float
) -> AuditRecord:
    """
    Validate a single ABTestSummary against reconstructed statistics.
    
    Args:
        summary: The ABTestSummary to validate
        reconstructed_p: The reconstructed p-value
        reconstructed_effect: The reconstructed effect size
        
    Returns:
        AuditRecord with validation results
    """
    warnings = []
    inconsistencies = []
    is_inconsistent = False
    sample_size_warning = None
    
    # Check sample size consistency
    sample_size_match, sample_size_error = check_sample_size_match(summary)
    if not sample_size_match:
        sample_size_warning = sample_size_error
        warnings.append({
            "code": ERR_SAMPLE_SIZE_MISMATCH,
            "message": f"Sample size issue: {sample_size_error}",
            "type": "data_quality_warning"
        })
    
    # Check p-value consistency
    p_consistent, p_error = validate_p_value_consistency(summary.reconstructed_p_value, reconstructed_p)
    if not p_consistent:
        is_inconsistent = True
        inconsistencies.append({
            "type": "p_value_inconsistency",
            "message": p_error,
            "reported_value": summary.reconstructed_p_value,
            "reconstructed_value": reconstructed_p
        })
    
    # Check effect size consistency
    baseline = calculate_effect_size_baseline(summary)
    effect_consistent, effect_error = validate_effect_size_consistency(
        summary.reconstructed_effect_size,
        reconstructed_effect,
        baseline
    )
    if not effect_consistent:
        is_inconsistent = True
        inconsistencies.append({
            "type": "effect_size_inconsistency",
            "message": effect_error,
            "reported_value": summary.reconstructed_effect_size,
            "reconstructed_value": reconstructed_effect,
            "baseline": baseline
        })
    
    # Create AuditRecord
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_binary=summary.is_binary,
        is_inconsistent=is_inconsistent,
        sample_size_warning=sample_size_warning,
        warnings=warnings,
        inconsistencies=inconsistencies,
        reconstructed_p_value=reconstructed_p,
        reconstructed_effect_size=reconstructed_effect,
        reported_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reconstructed_effect_size,
        validation_timestamp=datetime.utcnow().isoformat(),
        data_quality_warning=sample_size_warning is not None
    )
    
    return audit_record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: Dict[str, Dict[str, float]]
) -> List[AuditRecord]:
    """
    Validate all ABTestSummary objects against their reconstructed statistics.
    
    Args:
        summaries: List of ABTestSummary objects to validate
        reconstructed_results: Dictionary mapping URL to reconstructed p-value and effect size
        
    Returns:
        List of AuditRecord objects
    """
    audit_records = []
    
    for summary in summaries:
        url = summary.url
        
        if url not in reconstructed_results:
            logger.warning(f"No reconstruction results for {url}")
            continue
        
        recon = reconstructed_results[url]
        reconstructed_p = recon.get("p_value")
        reconstructed_effect = recon.get("effect_size")
        
        audit_record = validate_single_summary(summary, reconstructed_p, reconstructed_effect)
        audit_records.append(audit_record)
        
        if audit_record.sample_size_warning:
            logger.warning(f"Sample size warning for {url}: {audit_record.sample_size_warning}")
        
        if audit_record.is_inconsistent:
            logger.info(f"Inconsistency detected for {url}: {len(audit_record.inconsistencies)} issues")
    
    return audit_records


def should_exclude_from_prevalence(audit_record: AuditRecord) -> bool:
    """
    Determine if an audit record should be excluded from aggregate prevalence estimates.
    
    Per FR-004b: entries with sample-size mismatches are excluded.
    
    Args:
        audit_record: The AuditRecord to check
        
    Returns:
        True if the record should be excluded, False otherwise
    """
    return audit_record.sample_size_warning is not None


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> Dict[str, Any]:
    """
    Write audit records to a JSON report file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to write the JSON report
        
    Returns:
        Summary statistics of the audit
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert AuditRecords to dictionaries
    records_dict = []
    for record in audit_records:
        records_dict.append(record.to_dict())
    
    # Calculate summary statistics
    total_count = len(audit_records)
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    sample_size_warning_count = sum(1 for r in audit_records if r.sample_size_warning is not None)
    
    # Exclude sample-size mismatch entries from prevalence calculation
    valid_for_prevalence = [r for r in audit_records if not should_exclude_from_prevalence(r)]
    valid_count = len(valid_for_prevalence)
    valid_inconsistent_count = sum(1 for r in valid_for_prevalence if r.is_inconsistent)
    
    prevalence_rate = valid_inconsistent_count / valid_count if valid_count > 0 else 0.0
    overall_rate = inconsistent_count / total_count if total_count > 0 else 0.0
    
    summary = {
        "total_summaries": total_count,
        "inconsistent_count": inconsistent_count,
        "inconsistent_rate": overall_rate,
        "sample_size_warning_count": sample_size_warning_count,
        "valid_for_prevalence_count": valid_count,
        "valid_inconsistent_count": valid_inconsistent_count,
        "prevalence_rate_excluding_warnings": prevalence_rate,
        "generated_at": datetime.utcnow().isoformat(),
        "thresholds": {
            "absolute_p_difference": ABSOLUTE_P_DIFF_THRESHOLD,
            "relative_effect_size": RELATIVE_EFFECT_SIZE_THRESHOLD
        }
    }
    
    # Write the report
    report = {
        "summary": summary,
        "records": records_dict
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")
    logger.info(f"Total: {total_count}, Inconsistent: {inconsistent_count} ({overall_rate:.2%})")
    logger.info(f"Valid for prevalence: {valid_count}, Inconsistent: {valid_inconsistent_count} ({prevalence_rate:.2%})")
    
    return summary


def run_validator(
    summaries: List[ABTestSummary],
    reconstructed_results: Dict[str, Dict[str, float]],
    output_path: Path
) -> Dict[str, Any]:
    """
    Run the full validation pipeline.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_results: Dictionary of reconstruction results
        output_path: Path to write the audit report
        
    Returns:
        Summary statistics from the audit
    """
    logger.info(f"Starting validation for {len(summaries)} summaries")
    
    audit_records = validate_all_summaries(summaries, reconstructed_results)
    summary = write_audit_report(audit_records, output_path)
    
    return summary


def main():
    """
    Main entry point for the validator script.
    
    This function loads reconstructed results and summaries, runs validation,
    and writes the audit report to output/audit_report.json.
    """
    import argparse
    from code.src.audit.reconstructor import main as reconstructor_main
    from code.src.audit.extractor import main as extractor_main
    
    parser = argparse.ArgumentParser(description="Run inconsistency validator")
    parser.add_argument(
        "--summaries-path",
        type=Path,
        default=Path("data/processed/summaries.json"),
        help="Path to the summaries JSON file"
    )
    parser.add_argument(
        "--reconstruction-path",
        type=Path,
        default=Path("data/processed/reconstruction_results.json"),
        help="Path to the reconstruction results JSON file"
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to write the audit report"
    )
    
    args = parser.parse_args()
    
    # Load summaries
    if not args.summaries_path.exists():
        logger.error(f"Summaries file not found: {args.summaries_path}")
        return 1
    
    with open(args.summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**item) for item in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")
    
    # Load reconstruction results
    if not args.reconstruction_path.exists():
        logger.error(f"Reconstruction results file not found: {args.reconstruction_path}")
        return 1
    
    with open(args.reconstruction_path, 'r', encoding='utf-8') as f:
        reconstructed_results = json.load(f)
    
    logger.info(f"Loaded {len(reconstructed_results)} reconstruction results")
    
    # Run validation
    summary = run_validator(summaries, reconstructed_results, args.output_path)
    
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    exit(main())
