"""
Inconsistency Validator Module (FR-004).

Validates A/B test summaries by comparing reported metrics against
reconstructed statistical results. Flags inconsistencies based on:
1. Absolute p-value difference > 0.05
2. Relative effect-size difference > 5%

Additionally handles FR-004b: Excludes sample-size mismatch entries
from aggregate prevalence estimates and generates data_quality_warning
AuditRecords.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.helpers import safe_float, parse_inequality_p

# Thresholds defined in FR-004
THRESHOLD_ABS_P_DIFF = 0.05
THRESHOLD_REL_EFFECT_SIZE = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(reported_p: float, reconstructed_p: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(reported_p - reconstructed_p)


def calculate_relative_effect_size_difference(
    reported_effect: float, reconstructed_effect: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Returns 0.0 if both are zero to avoid division issues.
    """
    if reported_effect == 0 and reconstructed_effect == 0:
        return 0.0
    if reported_effect == 0:
        return 1.0  # Infinite relative difference if reported is 0 but reconstructed isn't
    
    return abs(reported_effect - reconstructed_effect) / abs(reported_effect)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if sample sizes in the summary are inconsistent or missing.
    Checks for negative values, zero values where expected > 0, 
    or conflicting total N vs group Ns if available.
    """
    n_control = safe_float(summary.n_control)
    n_treatment = safe_float(summary.n_treatment)
    
    # Basic validity checks
    if n_control is None or n_treatment is None:
        return True
    
    if n_control <= 0 or n_treatment <= 0:
        return True
        
    # If total N is provided, check consistency
    if summary.n_total is not None:
        n_total = safe_float(summary.n_total)
        if n_total is not None:
            expected_total = n_control + n_treatment
            if abs(n_total - expected_total) > 1: # Allow small float rounding error
                return True
                
    return False


def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, float, float]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    Returns (is_consistent, reported_p, reconstructed_p).
    """
    reported_p = parse_inequality_p(summary.reported_p_value)
    reconstructed_p = summary.reconstructed_p_value
    
    if reported_p is None or reconstructed_p is None:
        return False, reported_p, reconstructed_p
        
    diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
    is_consistent = diff <= THRESHOLD_ABS_P_DIFF
    
    return is_consistent, reported_p, reconstructed_p


def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, float, float]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    Returns (is_consistent, reported_effect, reconstructed_effect).
    """
    reported_effect = safe_float(summary.reported_effect_size)
    reconstructed_effect = summary.reconstructed_effect_size
    
    if reported_effect is None or reconstructed_effect is None:
        return False, reported_effect, reconstructed_effect
        
    diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
    is_consistent = diff <= THRESHOLD_REL_EFFECT_SIZE
    
    return is_consistent, reported_effect, reconstructed_effect


def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    is_effect_consistent: bool,
    has_sample_mismatch: bool,
    p_diff: float,
    effect_diff: float
) -> AuditRecord:
    """Create an AuditRecord based on validation results."""
    notes = []
    warnings = []
    
    if has_sample_mismatch:
        notes.append("Sample size mismatch detected.")
        warnings.append("data_quality_warning")
        
    if not is_p_consistent:
        notes.append(f"P-value inconsistency: diff={p_diff:.4f} > {THRESHOLD_ABS_P_DIFF}")
        
    if not is_effect_consistent:
        notes.append(f"Effect size inconsistency: rel_diff={effect_diff:.4f} > {THRESHOLD_REL_EFFECT_SIZE}")
        
    if not notes:
        notes.append("All metrics consistent within thresholds.")
        
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=(not is_p_consistent or not is_effect_consistent),
        notes="; ".join(notes),
        warnings=warnings if warnings else None,
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        sample_size_mismatch=has_sample_mismatch,
        timestamp=datetime.utcnow().isoformat()
    )


def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """Validate a single A/B test summary."""
    is_p_consistent, rep_p, rec_p = check_p_value_consistency(summary)
    is_effect_consistent, rep_e, rec_e = check_effect_size_consistency(summary)
    has_mismatch = detect_sample_size_mismatch(summary)
    
    p_diff = calculate_absolute_p_difference(rep_p, rec_p) if rep_p is not None and rec_p is not None else 0.0
    eff_diff = calculate_relative_effect_size_difference(rep_e, rec_e) if rep_e is not None and rec_e is not None else 0.0
    
    return create_audit_record(
        summary, is_p_consistent, is_effect_consistent, has_mismatch, p_diff, eff_diff
    )


def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate a list of summaries and return AuditRecords."""
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
        except Exception as e:
            logger.error(f"Error validating summary for {summary.url}: {e}")
            # Create a failed record
            records.append(AuditRecord(
                url=summary.url,
                domain=summary.domain,
                is_inconsistent=True,
                notes=f"Validation error: {str(e)}",
                warnings=["validation_error"],
                timestamp=datetime.utcnow().isoformat()
            ))
    return records


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter out records with sample_size_mismatch for prevalence calculations (FR-004b).
    """
    return [r for r in records if not r.sample_size_mismatch]


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write audit records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [
        {
            "url": r.url,
            "domain": r.domain,
            "is_inconsistent": r.is_inconsistent,
            "notes": r.notes,
            "warnings": r.warnings,
            "reported_p_value": r.reported_p_value,
            "reconstructed_p_value": r.reconstructed_p_value,
            "reported_effect_size": r.reported_effect_size,
            "reconstructed_effect_size": r.reconstructed_effect_size,
            "sample_size_mismatch": r.sample_size_mismatch,
            "timestamp": r.timestamp
        }
        for r in records
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Audit report written to {output_path}")


def main() -> None:
    """Main entry point for running the validator."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.audit.validator <input_summaries.json> <output_report.json>")
        sys.exit(1)
        
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    # Load summaries
    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
        
    # Convert to ABTestSummary objects (assuming the JSON structure matches)
    # In a real pipeline, this would come from the reconstructor output
    summaries = [ABTestSummary(**s) for s in summaries_data]
    
    # Validate
    records = validate_all_summaries(summaries)
    
    # Write report
    write_audit_report(records, output_path)
    
    # Log summary stats
    inconsistent_count = sum(1 for r in records if r.is_inconsistent)
    mismatch_count = sum(1 for r in records if r.sample_size_mismatch)
    logger.info(f"Validation complete. Total: {len(records)}, Inconsistent: {inconsistent_count}, Sample Mismatch: {mismatch_count}")


if __name__ == "__main__":
    main()
