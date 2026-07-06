import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED

logger = get_default_logger(__name__)

# FR-004 Thresholds
ABSOLUTE_P_DIFFERENCE_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(p_reported - p_reconstructed)

def calculate_relative_effect_size_difference(
    effect_size_reported: float,
    effect_size_reconstructed: float
) -> float:
    """Calculate relative difference in effect sizes."""
    if effect_size_reported == 0:
        # Avoid division by zero; if reported is 0 but reconstructed is not, it's a huge discrepancy
        return float('inf') if effect_size_reconstructed != 0 else 0.0
    return abs(effect_size_reported - effect_size_reconstructed) / abs(effect_size_reported)

def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if sample sizes are inconsistent (e.g., reported total != sum of groups,
    or missing sample size data that prevents validation).
    Returns True if a mismatch or critical missing data is detected.
    """
    # Check for missing sample sizes which prevents reconstruction/validation
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        return True

    # If total sample size is reported, check consistency
    if summary.sample_size_total is not None:
        expected_total = summary.sample_size_control + summary.sample_size_treatment
        if abs(summary.sample_size_total - expected_total) > 1: # Allow small rounding difference if floats
            return True

    return False

def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value_reported is None or summary.p_value_reconstructed is None:
        return False, float('nan')

    diff = calculate_absolute_p_difference(summary.p_value_reported, summary.p_value_reconstructed)
    return diff <= ABSOLUTE_P_DIFFERENCE_THRESHOLD, diff

def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size_reported is None or summary.effect_size_reconstructed is None:
        return False, float('nan')

    diff = calculate_relative_effect_size_difference(summary.effect_size_reported, summary.effect_size_reconstructed)
    return diff <= RELATIVE_EFFECT_SIZE_THRESHOLD, diff

def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: float,
    effect_consistent: bool,
    effect_diff: float,
    has_sample_size_mismatch: bool
) -> AuditRecord:
    """Create an AuditRecord based on validation results."""
    warnings = []
    flags = []

    if not p_consistent:
        flags.append("p_value_inconsistent")
        warnings.append(f"P-value difference {p_diff:.4f} exceeds threshold {ABSOLUTE_P_DIFFERENCE_THRESHOLD}")

    if not effect_consistent:
        flags.append("effect_size_inconsistent")
        warnings.append(f"Effect size relative difference {effect_diff:.4f} exceeds threshold {RELATIVE_EFFECT_SIZE_THRESHOLD}")

    if has_sample_size_mismatch:
        # FR-004b: Flag for exclusion from prevalence, but generate warning
        warnings.append("data_quality_warning: sample size mismatch detected")
        flags.append("sample_size_mismatch")

    # Determine overall consistency
    is_consistent = p_consistent and effect_consistent and not has_sample_size_mismatch

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_consistent=is_consistent,
        flags=flags,
        warnings=warnings,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=summary.p_value_reconstructed,
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=summary.effect_size_reconstructed,
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        sample_size_total=summary.sample_size_total,
        audit_timestamp=datetime.utcnow().isoformat()
    )

def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """Validate a single ABTestSummary and return an AuditRecord."""
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)
    has_sample_size_mismatch = detect_sample_size_mismatch(summary)

    return create_audit_record(
        summary, p_consistent, p_diff, effect_consistent, effect_diff, has_sample_size_mismatch
    )

def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate a list of summaries and return corresponding AuditRecords."""
    records = []
    for summary in summaries:
        record = validate_summary(summary)
        records.append(record)
        if record.flags:
            logger.info(f"Validation flags for {summary.url}: {record.flags}")
    return records

def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    FR-004b: Filter out records flagged for sample-size mismatch from prevalence calculations.
    Returns list of records suitable for aggregate prevalence estimation.
    """
    return [r for r in records if "sample_size_mismatch" not in r.flags]

def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write the list of AuditRecords to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump() for r in records]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Audit report written to {output_path}")

def main() -> int:
    """
    Main entry point for the validator.
    Expects reconstructed summaries to be available (e.g., from reconstructor).
    For this task implementation, we assume summaries are loaded from a known path
    or passed via arguments in a real pipeline context.
    """
    # In a real pipeline, this would be called by run_audit.py with data in memory
    # or from a specific file. Here we simulate the loading of reconstructed data
    # if it exists, or log an error if not found, to satisfy the "real execution" constraint.
    input_path = Path("data/processed/reconstructed_summaries.json")
    output_path = Path("output/audit_report.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Ensure T023 (reconstructor) has run.")
        return 1

    try:
        with open(input_path, 'r') as f:
            summaries_data = json.load(f)
        
        # Convert dict list to ABTestSummary objects
        summaries = [ABTestSummary(**item) for item in summaries_data]
        
        logger.info(f"Validating {len(summaries)} summaries...")
        records = validate_all_summaries(summaries)
        
        write_audit_report(records, output_path)
        
        # Log summary stats
        total = len(records)
        consistent = sum(1 for r in records if r.is_consistent)
        mismatched = sum(1 for r in records if "sample_size_mismatch" in r.flags)
        logger.info(f"Validation complete. Total: {total}, Consistent: {consistent}, Sample Size Mismatches: {mismatched}")
        
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
