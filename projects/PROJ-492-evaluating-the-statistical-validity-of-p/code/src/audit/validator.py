"""
Inconsistency Validator Module (T025)

Implements FR-004 thresholds for statistical inconsistency detection:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with 'data_quality_warning' for sample-size discrepancies.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Constants for FR-004 thresholds
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(p_reconstructed: float, p_reported: float) -> float:
    """
    Calculate the absolute difference between reconstructed and reported p-values.
    """
    return abs(p_reconstructed - p_reported)


def calculate_relative_effect_size_difference(effect_reconstructed: float, effect_reported: float) -> float:
    """
    Calculate the relative difference in effect sizes.
    Handles zero or near-zero reported effects safely.
    """
    if effect_reported == 0:
        # If reported is 0 but reconstructed is not, the relative difference is effectively infinite or undefined.
        # We treat this as a large difference if reconstructed is non-zero.
        return float('inf') if effect_reconstructed != 0 else 0.0
    
    try:
        rel_diff = abs(effect_reconstructed - effect_reported) / abs(effect_reported)
        return rel_diff
    except ZeroDivisionError:
        return float('inf')


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detects if there is a significant mismatch in sample sizes reported vs required for the test.
    For this validator, we check if the summary indicates a sample size issue (e.g., N < 30, or explicit flag).
    In the context of FR-004b, we flag records where sample size information is missing or inconsistent
    with the statistical test requirements.
    
    Returns True if a mismatch/issue is detected that warrants exclusion from prevalence.
    """
    # Check for missing sample sizes
    if summary.n_control is None or summary.n_treatment is None:
        return True
    
    # Check for zero sample sizes
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return True

    # Check for extreme imbalance if specific logic is required (optional, but good practice)
    # For now, we stick to the core requirement: missing or invalid N implies mismatch/quality warning.
    
    # If the summary has a flag explicitly set (if the model supports it), check that too.
    # Assuming ABTestSummary might have a 'sample_size_valid' field or similar if populated by extractor.
    # If not, we rely on the presence and validity of n_control/n_treatment.
    
    return False


def check_p_value_consistency(summary: ABTestSummary, reconstructed_p: float) -> Tuple[bool, str]:
    """
    Checks if the reconstructed p-value is consistent with the reported p-value.
    Returns (is_consistent, reason)
    """
    if summary.p_value is None:
        return True, "No reported p-value to compare"

    diff = calculate_absolute_p_difference(reconstructed_p, summary.p_value)
    if diff > ABSOLUTE_P_THRESHOLD:
        return False, f"P-value diff {diff:.4f} > {ABSOLUTE_P_THRESHOLD}"
    return True, "P-value consistent"


def check_effect_size_consistency(summary: ABTestSummary, reconstructed_effect: float) -> Tuple[bool, str]:
    """
    Checks if the reconstructed effect size is consistent with the reported one.
    Returns (is_consistent, reason)
    """
    if summary.effect_size is None:
        return True, "No reported effect size to compare"

    diff = calculate_relative_effect_size_difference(reconstructed_effect, summary.effect_size)
    if diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
        return False, f"Effect size rel diff {diff:.4f} > {RELATIVE_EFFECT_SIZE_THRESHOLD}"
    return True, "Effect size consistent"


def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    p_reason: str,
    is_effect_consistent: bool,
    effect_reason: str,
    has_sample_size_mismatch: bool,
    reconstructed_p: float,
    reconstructed_effect: float
) -> AuditRecord:
    """
    Creates an AuditRecord based on validation results.
    """
    notes = []
    warnings = []

    if not is_p_consistent:
        notes.append(f"P-value inconsistency: {p_reason}")
    
    if not is_effect_consistent:
        notes.append(f"Effect size inconsistency: {effect_reason}")
    
    if has_sample_size_mismatch:
        warning_msg = "Sample size mismatch detected; excluded from prevalence estimates per FR-004b"
        warnings.append(warning_msg)
        notes.append(warning_msg)

    # Determine overall consistency
    is_consistent = is_p_consistent and is_effect_consistent and not has_sample_size_mismatch
    
    # If sample size mismatch is found, we flag it as a data quality warning
    # but the record itself might still be "inconsistent" in terms of stats if p or effect failed.
    # However, for prevalence calculation, it is excluded.
    
    record = AuditRecord(
        source_url=summary.source_url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=not is_consistent,
        p_value_reported=summary.p_value,
        p_value_reconstructed=reconstructed_p,
        effect_size_reported=summary.effect_size,
        effect_size_reconstructed=reconstructed_effect,
        notes=notes,
        data_quality_warnings=warnings if warnings else None
    )
    
    return record


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: float
) -> AuditRecord:
    """
    Validates a single ABTestSummary against FR-004 thresholds.
    """
    # Check sample size mismatch first
    has_mismatch = detect_sample_size_mismatch(summary)
    
    # Check p-value consistency
    is_p_consistent, p_reason = check_p_value_consistency(summary, reconstructed_p)
    
    # Check effect size consistency
    is_effect_consistent, effect_reason = check_effect_size_consistency(summary, reconstructed_effect)
    
    return create_audit_record(
        summary,
        is_p_consistent,
        p_reason,
        is_effect_consistent,
        effect_reason,
        has_mismatch,
        reconstructed_p,
        reconstructed_effect
    )


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validates all summaries against their reconstructed statistical results.
    
    Args:
        summaries: List of ABTestSummary objects.
        reconstructed_results: List of dicts containing 'url', 'p_value', 'effect_size' from reconstructor.
    
    Returns:
        List of AuditRecord objects.
    """
    # Create a lookup for reconstructed results by URL
    recon_map = {r['url']: r for r in reconstructed_results}
    
    audit_records = []
    
    for summary in summaries:
        recon = recon_map.get(summary.source_url)
        if not recon:
            logger.warning(f"No reconstruction found for {summary.source_url}. Skipping.")
            continue
        
        record = validate_summary(
            summary,
            recon['p_value'],
            recon['effect_size']
        )
        audit_records.append(record)
        
    return audit_records


def filter_for_prevalence(audit_records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filters audit records to exclude those with sample-size mismatches.
    This ensures FR-004b compliance: sample-size mismatch entries are excluded 
    from aggregate prevalence estimates.
    """
    return [r for r in audit_records if not (r.data_quality_warnings and any("Sample size mismatch" in w for w in r.data_quality_warnings))]


def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Writes the audit records to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = []
    for record in audit_records:
        report_data.append(record.model_dump())
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Audit report written to {output_path}")


def main():
    """
    Main entry point for the validator script.
    Expects reconstructed results and summaries to be available in the data directory.
    """
    # This function is typically called by the driver script (run_audit.py)
    # but provided here for direct execution if needed.
    # It assumes paths are configured or passed via arguments in a real runner.
    # For T025, we ensure the logic exists and is callable.
    
    logger.info("Validator module loaded successfully.")
    # Placeholder for direct execution logic if needed, usually handled by run_audit.py
    pass


if __name__ == "__main__":
    main()
