"""
Inconsistency Validator Module.

Implements FR-004: Validates reconstructed statistical tests against reported values.
- Absolute p-value difference threshold: > 0.05
- Relative effect-size difference threshold: > 5%
- FR-004b: Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies.
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

# Constants for thresholds
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def check_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Checks if sample sizes are consistent within a single test summary.
    Returns (is_consistent, error_message).
    
    For binary tests, checks if n_control and n_treatment are positive and reasonable.
    For continuous tests, checks similar constraints.
    """
    if summary.n_control is None or summary.n_treatment is None:
        return False, "Missing sample sizes"
    
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return False, "Invalid sample sizes (must be positive)"
    
    # Check for extreme mismatches that might indicate data errors
    # e.g., one group is 100x larger than the other without explanation
    ratio = max(summary.n_control, summary.n_treatment) / min(summary.n_control, summary.n_treatment)
    if ratio > 100:
        return False, f"Extreme sample size mismatch (ratio {ratio:.1f} > 100)"
        
    return True, None


def calculate_p_value_difference(reconstructed_p: float, reported_p: float) -> float:
    """
    Calculates absolute difference between reconstructed and reported p-values.
    """
    if reconstructed_p is None or reported_p is None:
        return float('inf')
    return abs(reconstructed_p - reported_p)


def calculate_effect_size_difference(reconstructed_effect: float, reported_effect: float) -> float:
    """
    Calculates relative difference between reconstructed and reported effect sizes.
    Returns relative difference as a fraction (e.g., 0.05 for 5%).
    """
    if reconstructed_effect is None or reported_effect is None:
        return float('inf')
    
    # Avoid division by zero
    if abs(reported_effect) < 1e-10:
        return float('inf')
        
    relative_diff = abs(reconstructed_effect - reported_effect) / abs(reported_effect)
    return relative_diff


def validate_single_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validates a single ABTestSummary against its reported metrics.
    Returns an AuditRecord with consistency flags and warnings.
    """
    # Initialize flags
    is_p_consistent = True
    is_effect_consistent = True
    is_sample_size_consistent = True
    data_quality_warning = None
    inconsistency_reasons = []
    
    # Check sample size consistency first
    sample_ok, sample_err = check_sample_size_consistency(summary)
    if not sample_ok:
        is_sample_size_consistent = False
        data_quality_warning = f"Sample size issue: {sample_err}"
        inconsistency_reasons.append(f"Sample size mismatch: {sample_err}")
    
    # Calculate p-value difference
    reconstructed_p = summary.reconstructed_p_value
    reported_p = summary.reported_p_value
    
    if reconstructed_p is not None and reported_p is not None:
        p_diff = calculate_p_value_difference(reconstructed_p, reported_p)
        if p_diff > P_VALUE_THRESHOLD:
            is_p_consistent = False
            inconsistency_reasons.append(
                f"P-value discrepancy: |{reconstructed_p:.4f} - {reported_p:.4f}| = {p_diff:.4f} > {P_VALUE_THRESHOLD}"
            )
    
    # Calculate effect size difference
    reconstructed_effect = summary.reconstructed_effect_size
    reported_effect = summary.reported_effect_size
    
    if reconstructed_effect is not None and reported_effect is not None:
        effect_diff = calculate_effect_size_difference(reconstructed_effect, reported_effect)
        if effect_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            is_effect_consistent = False
            inconsistency_reasons.append(
                f"Effect size discrepancy: relative diff {effect_diff:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}"
            )
    
    # Determine overall consistency
    is_inconsistent = not (is_p_consistent and is_effect_consistent)
    
    # Create AuditRecord
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        test_type=summary.test_type,
        is_inconsistent=is_inconsistent,
        p_value_consistent=is_p_consistent,
        effect_size_consistent=is_effect_consistent,
        sample_size_consistent=is_sample_size_consistent,
        data_quality_warning=data_quality_warning,
        inconsistency_reasons=inconsistency_reasons,
        reconstructed_p_value=reconstructed_p,
        reported_p_value=reported_p,
        reconstructed_effect_size=reconstructed_effect,
        reported_effect_size=reported_effect,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        validation_timestamp=datetime.utcnow().isoformat(),
        source_file=summary.source_file if hasattr(summary, 'source_file') else None
    )
    
    return audit_record


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Validates a list of ABTestSummary objects.
    Returns a list of AuditRecord objects.
    """
    audit_records = []
    for summary in summaries:
        record = validate_single_summary(summary)
        audit_records.append(record)
    return audit_records


def get_prevalence_records(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filters audit records to exclude those with sample-size mismatches
    for the purpose of calculating aggregate prevalence estimates (FR-004b).
    """
    return [record for record in audit_records if record.sample_size_consistent]


def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Writes the audit records to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(audit_records),
            "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
            "sample_size_warning_count": sum(1 for r in audit_records if not r.sample_size_consistent),
            "thresholds": {
                "p_value_absolute_diff": P_VALUE_THRESHOLD,
                "effect_size_relative_diff": EFFECT_SIZE_RELATIVE_THRESHOLD
            }
        },
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "test_type": r.test_type,
                "is_inconsistent": r.is_inconsistent,
                "p_value_consistent": r.p_value_consistent,
                "effect_size_consistent": r.effect_size_consistent,
                "sample_size_consistent": r.sample_size_consistent,
                "data_quality_warning": r.data_quality_warning,
                "inconsistency_reasons": r.inconsistency_reasons,
                "reconstructed_p_value": r.reconstructed_p_value,
                "reported_p_value": r.reported_p_value,
                "reconstructed_effect_size": r.reconstructed_effect_size,
                "reported_effect_size": r.reported_effect_size,
                "n_control": r.n_control,
                "n_treatment": r.n_treatment,
                "validation_timestamp": r.validation_timestamp,
                "source_file": r.source_file
            }
            for r in audit_records
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Audit report written to {output_path}")


def run_validator(
    summaries_path: Path,
    output_path: Path,
    log_level: str = "INFO"
) -> List[AuditRecord]:
    """
    Main entry point for the validator.
    
    Args:
        summaries_path: Path to JSON file containing ABTestSummary objects
        output_path: Path where audit_report.json will be written
        log_level: Logging level
        
    Returns:
        List of AuditRecord objects
    """
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Load summaries
    if not summaries_path.exists():
        raise FileNotFoundError(f"Summaries file not found: {summaries_path}")
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    # Convert to ABTestSummary objects
    # Assuming the JSON structure matches ABTestSummary fields
    summaries = []
    for item in summaries_data:
        try:
            summary = ABTestSummary(**item)
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to parse summary: {e}")
            continue
    
    logger.info(f"Loaded {len(summaries)} summaries for validation")
    
    # Validate
    audit_records = validate_all_summaries(summaries)
    
    # Write report
    write_audit_report(audit_records, output_path)
    
    # Log summary
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    sample_warning_count = sum(1 for r in audit_records if not r.sample_size_consistent)
    logger.info(f"Validation complete: {inconsistent_count} inconsistent, {sample_warning_count} with sample size warnings")
    
    return audit_records


def main():
    """
    CLI entry point for the validator.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries for statistical inconsistency")
    parser.add_argument("--input", type=Path, required=True, help="Path to reconstructed summaries JSON")
    parser.add_argument("--output", type=Path, default=Path("output/audit_report.json"), help="Path to output audit report")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    try:
        run_validator(args.input, args.output, args.log_level)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
