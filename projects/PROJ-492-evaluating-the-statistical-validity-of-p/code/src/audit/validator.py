"""
Inconsistency Validator Module.

Implements FR-004: Validates reconstructed statistical results against reported values.
- Absolute p-value difference threshold: > 0.05
- Relative effect-size difference threshold: > 5%
- FR-004b: Flags sample-size mismatches and excludes them from aggregate prevalence estimates.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

# Thresholds from FR-004
P_VALUE_ABSOLUTE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_relative_difference(val1: Optional[float], val2: Optional[float]) -> Optional[float]:
    """
    Calculates the relative difference between two values.
    Returns None if either is None or if the denominator is zero.
    Formula: |val1 - val2| / max(|val1|, |val2|, epsilon)
    """
    if val1 is None or val2 is None:
        return None
    
    denom = max(abs(val1), abs(val2))
    if denom < 1e-9:
        # If both are effectively zero, relative diff is undefined or 0. 
        # If one is 0 and other is not, diff is 1.0 (100%).
        if abs(val1 - val2) < 1e-9:
            return 0.0
        return 1.0
    
    return abs(val1 - val2) / denom


def validate_single_summary(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> Tuple[bool, List[str], bool]:
    """
    Validates a single ABTestSummary against its reconstructed statistics.
    
    Returns:
      - is_consistent: True if no thresholds are violated.
      - warnings: List of warning messages.
      - has_sample_size_mismatch: True if sample sizes differ significantly.
    """
    warnings = []
    is_consistent = True
    has_sample_size_mismatch = False

    # 1. Check Sample Size Mismatch (FR-004b)
    # We consider a mismatch if the reported sample size differs from the 
    # one used in reconstruction (if available) or if the summary itself 
    # has conflicting internal sample sizes (e.g., n_control vs n_treatment missing).
    # For this validator, we assume 'reconstructed' contains the 'n_control' and 'n_treatment' 
    # used for the calculation.
    rec_n_control = reconstructed.get('n_control')
    rec_n_treatment = reconstructed.get('n_treatment')
    rep_n_control = summary.n_control
    rep_n_treatment = summary.n_treatment

    if rec_n_control is not None and rep_n_control is not None and rec_n_control != rep_n_control:
        warnings.append(f"Sample size mismatch (control): reported={rep_n_control}, reconstructed={rec_n_control}")
        has_sample_size_mismatch = True
        is_consistent = False # Sample size mismatch is a data quality issue, flagging it as inconsistency for audit
    
    if rec_n_treatment is not None and rep_n_treatment is not None and rec_n_treatment != rep_n_treatment:
        warnings.append(f"Sample size mismatch (treatment): reported={rep_n_treatment}, reconstructed={rec_n_treatment}")
        has_sample_size_mismatch = True
        is_consistent = False

    # 2. Check P-value Consistency (FR-004)
    reported_p = summary.p_value
    reconstructed_p = reconstructed.get('p_value')

    if reported_p is not None and reconstructed_p is not None:
        abs_diff = abs(reported_p - reconstructed_p)
        if abs_diff > P_VALUE_ABSOLUTE_THRESHOLD:
            warnings.append(
                f"P-value inconsistency: reported={reported_p:.4f}, reconstructed={reconstructed_p:.4f}, "
                f"abs_diff={abs_diff:.4f} > {P_VALUE_ABSOLUTE_THRESHOLD}"
            )
            is_consistent = False
    elif reported_p is None:
        warnings.append("Missing reported p-value; cannot validate consistency.")
        # Not necessarily an inconsistency in the *calculation*, but a data quality warning
        # However, per FR-004, we are checking validity. If we can't check, we flag it.
        # For strict compliance, we might not mark as 'inconsistent' but add a warning.
        # Let's add warning but not set is_consistent=False unless it implies a missing metric.
        # But usually, missing metric = data quality issue.
    
    # 3. Check Effect Size Consistency (FR-004)
    reported_effect = summary.effect_size
    reconstructed_effect = reconstructed.get('effect_size')

    if reported_effect is not None and reconstructed_effect is not None:
        rel_diff = calculate_relative_difference(reported_effect, reconstructed_effect)
        if rel_diff is not None and rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            warnings.append(
                f"Effect size inconsistency: reported={reported_effect:.4f}, reconstructed={reconstructed_effect:.4f}, "
                f"rel_diff={rel_diff:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}"
            )
            is_consistent = False
    elif reported_effect is None:
        warnings.append("Missing reported effect size; cannot validate consistency.")

    return is_consistent, warnings, has_sample_size_mismatch


def run_validator(summaries: List[ABTestSummary], reconstructed_results: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Runs validation on a list of summaries against reconstructed results.
    
    Args:
      summaries: List of ABTestSummary objects extracted from web.
      reconstructed_results: List of dicts containing reconstructed stats (p_value, effect_size, n_control, n_treatment).
      
    Returns:
      List of AuditRecord objects.
    """
    audit_records = []
    
    if len(summaries) != len(reconstructed_results):
        logger.error(f"Length mismatch: {len(summaries)} summaries vs {len(reconstructed_results)} reconstructions")
        raise ValueError("Summaries and reconstructed results must have the same length.")

    for i, summary in enumerate(summaries):
        rec = reconstructed_results[i]
        is_consistent, warnings, has_sample_size_mismatch = validate_single_summary(summary, rec)
        
        # Determine data_quality_warning
        data_quality_warning = None
        if has_sample_size_mismatch:
            data_quality_warning = "Sample size mismatch detected; excluded from aggregate prevalence estimates per FR-004b."
            # Log the specific warning
            logger.warning(f"Record {summary.url}: {data_quality_warning}")
        elif not is_consistent and not has_sample_size_mismatch:
            # Statistical inconsistency found
            data_quality_warning = "Statistical inconsistency detected (p-value or effect size)."

        # Create AuditRecord
        # We assume the 'reconstructed' dict has a 'method' key or we infer it.
        # For simplicity, we construct the record.
        audit_record = AuditRecord(
            url=summary.url,
            domain=summary.domain,
            year=summary.year,
            reported_p_value=summary.p_value,
            reconstructed_p_value=rec.get('p_value'),
            reported_effect_size=summary.effect_size,
            reconstructed_effect_size=rec.get('effect_size'),
            is_consistent=is_consistent,
            warnings=warnings,
            data_quality_warning=data_quality_warning,
            timestamp=datetime.utcnow().isoformat()
        )
        audit_records.append(audit_record)

    return audit_records


def write_audit_report(audit_records: List[AuditRecord], output_path: str) -> None:
    """
    Writes the list of AuditRecord objects to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert dataclasses to dicts
    records_dict = [asdict(record) for record in audit_records]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_dict, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_file}")


def main():
    """
    Entry point for the validator.
    Expects reconstructed results to be loaded from a specific location or passed as arguments.
    For this implementation, we assume a standard path for reconstructed data if not provided.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the inconsistency validator.")
    parser.add_argument("--summaries", type=str, default="data/processed/extracted_summaries.json",
                        help="Path to extracted summaries JSON.")
    parser.add_argument("--reconstructed", type=str, default="data/processed/reconstructed_stats.json",
                        help="Path to reconstructed statistics JSON.")
    parser.add_argument("--output", type=str, default="output/audit_report.json",
                        help="Path to output audit report JSON.")
    
    args = parser.parse_args()
    
    # Load data
    try:
        with open(args.summaries, 'r') as f:
            summaries_data = json.load(f)
        summaries = [ABTestSummary(**item) for item in summaries_data]
    except Exception as e:
        logger.error(f"Failed to load summaries: {e}")
        return 1
    
    try:
        with open(args.reconstructed, 'r') as f:
            reconstructed_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load reconstructed data: {e}")
        return 1
    
    # Run validation
    audit_records = run_validator(summaries, reconstructed_data)
    
    # Write report
    write_audit_report(audit_records, args.output)
    
    # Summary stats
    total = len(audit_records)
    consistent = sum(1 for r in audit_records if r.is_consistent)
    warnings = sum(1 for r in audit_records if r.data_quality_warning)
    
    logger.info(f"Validation complete: {total} records. Consistent: {consistent}, Warnings: {warnings}")
    
    return 0


if __name__ == "__main__":
    exit(main())
