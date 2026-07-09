"""
Inconsistency validator for A/B test summaries.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05
- Relative effect-size > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED, set_rng_seed

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)

def compute_effect_size(summary: ABTestSummary) -> Optional[float]:
    """
    Compute the relative effect size (lift) for a given summary.
    
    Effect size = (treatment_rate - control_rate) / control_rate
    Returns None if control_rate is 0 or missing.
    """
    if summary.control_rate is None or summary.treatment_rate is None:
        return None
    if summary.control_rate == 0:
        return None
    
    return (summary.treatment_rate - summary.control_rate) / summary.control_rate

def check_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check if sample sizes are consistent between control and treatment groups.
    
    Returns:
        Tuple of (is_consistent, warning_message)
        - If inconsistent, returns (False, warning_message)
        - If consistent or cannot determine, returns (True, None)
    """
    if summary.control_n is None or summary.treatment_n is None:
        # Cannot determine consistency if sample sizes are missing
        return True, None
    
    # Check for significant mismatch (e.g., > 10% difference)
    # This is a heuristic; the exact threshold may vary by context
    max_n = max(summary.control_n, summary.treatment_n)
    min_n = min(summary.control_n, summary.treatment_n)
    
    if max_n == 0:
        return True, None
    
    ratio = min_n / max_n
    
    # If the smaller group is less than 90% of the larger group, flag as mismatch
    if ratio < 0.9:
        warning = f"Sample size mismatch detected: control_n={summary.control_n}, treatment_n={summary.treatment_n} (ratio={ratio:.2f})"
        return False, warning
    
    return True, None

def validate_single_summary(
    summary: ABTestSummary, 
    reconstructed_p_value: float,
    reconstructed_effect_size: Optional[float] = None
) -> AuditRecord:
    """
    Validate a single A/B test summary against FR-004 thresholds.
    
    Args:
        summary: The ABTestSummary object to validate
        reconstructed_p_value: The p-value reconstructed from raw data
        reconstructed_effect_size: Optional reconstructed effect size
    
    Returns:
        AuditRecord with validation results
    """
    set_rng_seed(SEED)
    
    is_inconsistent = False
    reasons = []
    data_quality_warnings = []
    
    # Check sample size consistency (FR-004b)
    sample_consistent, sample_warning = check_sample_size_consistency(summary)
    if not sample_consistent:
        data_quality_warnings.append(sample_warning)
        # Note: We still flag inconsistency but mark it as a data quality issue
        is_inconsistent = True
        reasons.append("Sample size mismatch")
    
    # Check p-value consistency
    reported_p = summary.reported_p_value
    if reported_p is not None and reconstructed_p_value is not None:
        p_diff = abs(reported_p - reconstructed_p_value)
        if p_diff > P_VALUE_THRESHOLD:
            is_inconsistent = True
            reasons.append(f"P-value discrepancy: |{reported_p} - {reconstructed_p_value}| = {p_diff:.4f} > {P_VALUE_THRESHOLD}")
    
    # Check effect size consistency if available
    if reconstructed_effect_size is not None:
        reported_effect = compute_effect_size(summary)
        if reported_effect is not None:
            # Relative difference in effect size
            if abs(reported_effect) > 0:
                effect_diff_rel = abs(reconstructed_effect_size - reported_effect) / abs(reported_effect)
                if effect_diff_rel > EFFECT_SIZE_RELATIVE_THRESHOLD:
                    is_inconsistent = True
                    reasons.append(f"Effect size discrepancy: relative difference = {effect_diff_rel:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}")
            else:
                # If reported effect is 0, check absolute difference
                if abs(reconstructed_effect_size) > abs(reported_effect) * (1 + EFFECT_SIZE_RELATIVE_THRESHOLD):
                    is_inconsistent = True
                    reasons.append(f"Effect size discrepancy: absolute difference too large")
    
    # Determine inconsistency type
    inconsistency_type = None
    if "P-value discrepancy" in str(reasons):
        inconsistency_type = "p_value_mismatch"
    elif "Effect size discrepancy" in str(reasons):
        inconsistency_type = "effect_size_mismatch"
    elif "Sample size mismatch" in str(reasons):
        inconsistency_type = "sample_size_mismatch"
    
    audit_record = AuditRecord(
        url=summary.url,
          domain=summary.domain,
          year=summary.year,
          is_inconsistent=is_inconsistent,
          inconsistency_type=inconsistency_type,
          reasons=reasons,
          data_quality_warnings=data_quality_warnings,
          reported_p_value=summary.reported_p_value,
          reconstructed_p_value=reconstructed_p_value,
          reported_effect_size=compute_effect_size(summary),
          reconstructed_effect_size=reconstructed_effect_size,
          sample_size_consistent=sample_consistent,
          validation_timestamp=datetime.utcnow().isoformat(),
          seed_used=SEED
    )
    
    return audit_record

def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: Dict[str, Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries against FR-004 thresholds.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_results: Dict mapping URL to reconstruction results
            {url: {"p_value": float, "effect_size": Optional[float]}}
    
    Returns:
        List of AuditRecord objects
    """
    audit_records = []
    
    for summary in summaries:
        url = summary.url
        if url not in reconstructed_results:
            logger.warning(f"No reconstruction results for URL: {url}")
            continue
        
        recon = reconstructed_results[url]
        recon_p = recon.get("p_value")
        recon_effect = recon.get("effect_size")
        
        record = validate_single_summary(summary, recon_p, recon_effect)
        audit_records.append(record)
        
        if record.data_quality_warnings:
            logger.warning(f"Data quality warnings for {url}: {record.data_quality_warnings}")
        if record.is_inconsistent:
            logger.info(f"Inconsistent test found: {url} - {record.reasons}")
    
    return audit_records

def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with sample-size mismatches
    for use in aggregate prevalence estimates (FR-004b).
    
    Args:
        audit_records: List of all AuditRecord objects
    
    Returns:
        List of AuditRecord objects without sample-size mismatches
    """
    filtered = [
        record for record in audit_records
        if record.sample_size_consistent
    ]
    
    excluded_count = len(audit_records) - len(filtered)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records with sample-size mismatches from prevalence calculation")
    
    return filtered

def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
    """
    Write audit records to a JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(audit_records),
        "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
        "sample_size_mismatch_count": sum(1 for r in audit_records if not r.sample_size_consistent),
        "records": [asdict(record) for record in audit_records]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")

def main():
    """
    Main entry point for the validator.
    
    This function:
    1. Loads reconstructed results from output/reconstructed_results.json
    2. Loads summaries from output/extracted_summaries.json
    3. Validates each summary against FR-004 thresholds
    4. Writes audit report to output/audit_report.json
    """
    project_root = Path(__file__).parent.parent.parent.parent
    input_summaries_path = project_root / "output" / "extracted_summaries.json"
    input_recon_path = project_root / "output" / "reconstructed_results.json"
    output_report_path = project_root / "output" / "audit_report.json"
    
    if not input_summaries_path.exists():
        logger.error(f"Input summaries file not found: {input_summaries_path}")
        return 1
    
    if not input_recon_path.exists():
        logger.error(f"Reconstructed results file not found: {input_recon_path}")
        return 1
    
    # Load data
    with open(input_summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    with open(input_recon_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)
    
    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in summaries_data]
    
    # Validate
    audit_records = validate_all_summaries(summaries, reconstructed_data)
    
    # Write report
    write_audit_report(audit_records, output_report_path)
    
    # Print summary
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    sample_mismatch = sum(1 for r in audit_records if not r.sample_size_consistent)
    prevalence_eligible = total - sample_mismatch
    
    logger.info(f"Validation complete:")
    logger.info(f"  Total records: {total}")
    logger.info(f"  Inconsistent: {inconsistent} ({inconsistent/total*100:.1f}%)")
    logger.info(f"  Sample size mismatches: {sample_mismatch}")
    logger.info(f"  Eligible for prevalence: {prevalence_eligible}")
    
    return 0

if __name__ == "__main__":
    exit(main())
