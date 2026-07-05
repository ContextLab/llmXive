"""
Inconsistency Validator Module.

Implements FR-004: Validates reconstructed statistical results against reported metrics.
Applies thresholds: absolute p-difference > 0.05, relative effect-size > 5%.
Implements FR-004b: Excludes sample-size mismatch entries from aggregate prevalence.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for thresholds
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)

def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    if p_reported is None or p_reconstructed is None:
        return float('inf')
    return abs(p_reported - p_reconstructed)

def calculate_relative_effect_size_difference(
    effect_reported: float,
    effect_reconstructed: float
) -> float:
    """Calculate relative difference in effect sizes."""
    if effect_reported is None or effect_reconstructed is None:
        return float('inf')
    if abs(effect_reported) < 1e-9:
        # Avoid division by zero; use absolute difference if baseline is near zero
        return abs(effect_reported - effect_reconstructed)
    return abs((effect_reported - effect_reconstructed) / effect_reported)

def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a mismatch in reported vs reconstructed sample sizes.
    Returns True if a mismatch is detected.
    """
    if summary.reported_n_control is None or summary.reconstructed_n_control is None:
        return False  # Cannot detect mismatch if data is missing

    if summary.reported_n_treatment is None or summary.reconstructed_n_treatment is None:
        return False

    # Allow small floating point tolerance for integer-like floats
    tolerance = 1e-5
    n_control_diff = abs(summary.reported_n_control - summary.reconstructed_n_control)
    n_treatment_diff = abs(summary.reported_n_treatment - summary.reconstructed_n_treatment)

    # If difference is significant relative to the size (e.g., > 1% or > 5 units)
    if n_control_diff > max(5, summary.reported_n_control * 0.01):
        return True
    if n_treatment_diff > max(5, summary.reported_n_treatment * 0.01):
        return True

    return False

def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if p-values are consistent within threshold.
    Returns (is_consistent, absolute_difference).
    """
    diff = calculate_absolute_p_difference(summary.reported_p_value, summary.reconstructed_p_value)
    is_consistent = diff <= ABSOLUTE_P_THRESHOLD
    return is_consistent, diff

def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if effect sizes are consistent within threshold.
    Returns (is_consistent, relative_difference).
    """
    diff = calculate_relative_effect_size_difference(
        summary.reported_effect_size,
        summary.reconstructed_effect_size
    )
    is_consistent = diff <= RELATIVE_EFFECT_SIZE_THRESHOLD
    return is_consistent, diff

def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    effect_consistent: bool,
    sample_size_mismatch: bool,
    p_diff: float,
    effect_diff: float
) -> AuditRecord:
    """
    Create an AuditRecord based on validation results.
    Implements FR-004b: Flags sample-size mismatches for exclusion.
    """
    is_inconsistent = not (p_consistent and effect_consistent)
    warnings = []
    exclusion_reason = None

    if not p_consistent:
        warnings.append(f"P-value discrepancy: {p_diff:.4f} > {ABSOLUTE_P_THRESHOLD}")
    if not effect_consistent:
        warnings.append(f"Effect size discrepancy: {effect_diff:.4f} > {RELATIVE_EFFECT_SIZE_THRESHOLD}")
    
    if sample_size_mismatch:
        warnings.append("Sample size mismatch detected")
        exclusion_reason = "sample_size_mismatch"
        # FR-004b: Flag for data quality warning and exclusion
        warnings.insert(0, "Data Quality Warning: Sample size mismatch")

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        is_inconsistent=is_inconsistent,
        data_quality_warning=len(warnings) > 0,
        audit_notes="; ".join(warnings) if warnings else None,
        exclusion_reason=exclusion_reason,
        validation_timestamp=datetime.utcnow().isoformat()
    )

def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """Validate a single summary and return an AuditRecord."""
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)
    sample_size_mismatch = detect_sample_size_mismatch(summary)

    return create_audit_record(
        summary, p_consistent, effect_consistent, sample_size_mismatch, p_diff, effect_diff
    )

def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate a list of summaries."""
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
            if record.data_quality_warning:
                logger.info(f"Warning for {summary.url}: {record.audit_notes}")
        except Exception as e:
            logger.error(f"Error validating {summary.url}: {e}", exc_info=True)
            # Create a failure record
            records.append(AuditRecord(
                url=summary.url,
                domain=summary.domain,
                reported_p_value=summary.reported_p_value,
                reconstructed_p_value=None,
                reported_effect_size=summary.reported_effect_size,
                reconstructed_effect_size=None,
                is_inconsistent=True,
                data_quality_warning=True,
                audit_notes=f"Validation error: {str(e)}",
                exclusion_reason="validation_error",
                validation_timestamp=datetime.utcnow().isoformat()
            ))
    return records

def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter records to exclude those with sample-size mismatches for prevalence calculation.
    Implements FR-004b.
    """
    return [r for r in records if r.exclusion_reason != "sample_size_mismatch"]

def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write audit records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = [record.dict() for record in records]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)
    logger.info(f"Audit report written to {output_path}")

def main() -> None:
    """Entry point for the validator script."""
    # Default paths
    input_path = Path("data/processed/extracted_summaries.json")
    output_path = Path("output/audit_report.json")

    # Allow CLI override if arguments were passed (simple check)
    import sys
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load summaries
    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in summaries_data]

    logger.info(f"Validating {len(summaries)} summaries...")
    records = validate_all_summaries(summaries)

    # Filter for prevalence (excluding sample size mismatches)
    valid_for_prevalence = filter_for_prevalence(records)
    logger.info(f"Excluded {len(records) - len(valid_for_prevalence)} records due to sample size mismatch.")

    # Write report
    write_audit_report(records, output_path)

    # Log summary stats
    inconsistent_count = sum(1 for r in records if r.is_inconsistent)
    warning_count = sum(1 for r in records if r.data_quality_warning)
    logger.info(f"Validation complete. Total: {len(records)}, Inconsistent: {inconsistent_count}, Warnings: {warning_count}")

if __name__ == "__main__":
    main()