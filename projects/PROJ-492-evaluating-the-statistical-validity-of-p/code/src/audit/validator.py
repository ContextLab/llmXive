"""
Inconsistency Validator Module (T025)

Implements FR-004 thresholds:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning for sample-size discrepancies.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED


def calculate_relative_difference(value1: float, value2: float) -> float:
    """
    Calculates the relative difference between two values.
    Returns 0.0 if both are zero to avoid division errors, or if denominator is zero.
    Formula: |value1 - value2| / max(|value1|, |value2|) if max != 0 else 0.0
    """
    if value1 is None or value2 is None:
        return 0.0
    
    abs_diff = abs(value1 - value2)
    max_val = max(abs(value1), abs(value2))
    
    if max_val == 0.0:
        return 0.0
    
    return abs_diff / max_val


def check_sample_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Checks if sample sizes are consistent within the summary.
    Returns (is_consistent, error_message).
    
    Specific checks:
    1. n_control and n_treatment must be positive integers.
    2. If reported p-value exists but sample sizes are missing, it's a mismatch.
    3. If effect size is reported but sample sizes are missing, it's a mismatch.
    """
    if summary.n_control is None or summary.n_treatment is None:
        # If we have metrics but no sample sizes, it's a quality issue
        if summary.p_value_reported is not None or summary.effect_size_reported is not None:
            return False, "Sample sizes missing but metrics reported"
        return True, None

    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return False, "Non-positive sample sizes detected"
    
    # Additional logic could check for extreme imbalances if required by spec
    return True, None


def validate_single_summary(
    summary: ABTestSummary, 
    reconstructed_p_value: Optional[float],
    reconstructed_effect_size: Optional[float]
) -> AuditRecord:
    """
    Validates a single ABTestSummary against FR-004 thresholds.
    
    Args:
        summary: The extracted summary object.
        reconstructed_p_value: The p-value calculated from raw data by reconstructor.
        reconstructed_effect_size: The effect size calculated from raw data.
        
    Returns:
        An AuditRecord object containing validation results.
    """
    logger = get_default_logger()
    is_inconsistent = False
    warnings = []
    reasons = []
    
    # 1. Check Sample Size Consistency (FR-004b prerequisite)
    sample_size_ok, sample_size_error = check_sample_size_consistency(summary)
    has_sample_size_mismatch = False
    
    if not sample_size_ok:
        has_sample_size_mismatch = True
        warnings.append(f"Sample size issue: {sample_size_error}")
        # Per FR-004b, we flag this but continue to check statistical consistency if possible
        # However, for prevalence calculation, this record will be excluded later.
    
    # 2. Check P-value Consistency (FR-004)
    # Threshold: absolute p-difference > 0.05
    p_diff = None
    if summary.p_value_reported is not None and reconstructed_p_value is not None:
        p_diff = abs(summary.p_value_reported - reconstructed_p_value)
        if p_diff > 0.05:
            is_inconsistent = True
            reasons.append(f"P-value mismatch: reported={summary.p_value_reported:.4f}, reconstructed={reconstructed_p_value:.4f}, diff={p_diff:.4f}")
            warnings.append("P-value inconsistency detected (diff > 0.05)")
    
    # 3. Check Effect Size Consistency (FR-004)
    # Threshold: relative effect-size > 5%
    es_diff = None
    if summary.effect_size_reported is not None and reconstructed_effect_size is not None:
        es_diff = calculate_relative_difference(summary.effect_size_reported, reconstructed_effect_size)
        if es_diff > 0.05:
            is_inconsistent = True
            reasons.append(f"Effect size mismatch: reported={summary.effect_size_reported}, reconstructed={reconstructed_effect_size}, rel_diff={es_diff:.4f}")
            warnings.append("Effect size inconsistency detected (rel diff > 5%)")
    
    # Construct the AuditRecord
    # If there is a sample size mismatch, we still generate the record but mark it with a warning.
    # The exclusion from prevalence happens at the aggregation level (see filter_for_prevalence).
    
    data_quality_warning = None
    if has_sample_size_mismatch:
        data_quality_warning = "Sample size mismatch or missing; excluded from prevalence estimates per FR-004b"
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=reconstructed_p_value,
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=reconstructed_effect_size,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        p_difference=p_diff,
        effect_size_difference=es_diff,
        reasons=reasons,
        warnings=warnings,
        data_quality_warning=data_quality_warning,
        validated_at=datetime.utcnow().isoformat()
    )


def validate_all_summaries(
    summaries: List[ABTestSummary], 
    reconstructed_results: Dict[str, Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validates a list of summaries against their reconstructed statistics.
    
    Args:
        summaries: List of extracted ABTestSummary objects.
        reconstructed_results: Dict mapping URL to {p_value, effect_size}.
        
    Returns:
        List of AuditRecord objects.
    """
    records = []
    logger = get_default_logger()
    
    for summary in summaries:
        url = summary.url
        recon = reconstructed_results.get(url, {})
        recon_p = recon.get("p_value")
        recon_es = recon.get("effect_size")
        
        record = validate_single_summary(summary, recon_p, recon_es)
        records.append(record)
        
        if record.is_inconsistent:
            logger.info(f"Inconsistency found for {url}: {record.reasons}")
        elif record.data_quality_warning:
            logger.warning(f"Data quality warning for {url}: {record.data_quality_warning}")
    
    return records


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filters audit records to exclude those with sample-size mismatches for prevalence estimation (FR-004b).
    
    Args:
        records: List of AuditRecord objects.
        
    Returns:
        List of AuditRecord objects suitable for prevalence calculation.
    """
    return [r for r in records if r.data_quality_warning is None]


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """
    Writes the list of AuditRecord objects to a JSON file.
    
    Args:
        records: List of AuditRecord objects.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert AuditRecord objects to dictionaries for JSON serialization
    serializable_records = []
    for r in records:
        serializable_records.append({
            "url": r.url,
            "domain": r.domain,
            "year": r.year,
            "is_inconsistent": r.is_inconsistent,
            "p_value_reported": r.p_value_reported,
            "p_value_reconstructed": r.p_value_reconstructed,
            "effect_size_reported": r.effect_size_reported,
            "effect_size_reconstructed": r.effect_size_reconstructed,
            "n_control": r.n_control,
            "n_treatment": r.n_treatment,
            "p_difference": r.p_difference,
            "effect_size_difference": r.effect_size_difference,
            "reasons": r.reasons,
            "warnings": r.warnings,
            "data_quality_warning": r.data_quality_warning,
            "validated_at": r.validated_at
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_records, f, indent=2)
    
    logging.info(f"Audit report written to {output_path}")


def main():
    """
    Main entry point for the validator script.
    Expects reconstructed results and summaries to be available or passed via arguments.
    For the pipeline integration, this is called by run_audit.py.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inconsistency validator on reconstructed data.")
    parser.add_argument("--summaries", type=str, required=True, help="Path to extracted summaries JSON")
    parser.add_argument("--reconstructed", type=str, required=True, help="Path to reconstructed results JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output audit report JSON")
    
    args = parser.parse_args()
    
    logger = get_default_logger()
    
    # Load summaries
    summaries = []
    with open(args.summaries, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            # Reconstruct ABTestSummary from dict
            summary = ABTestSummary(
                url=item.get("url"),
                domain=item.get("domain"),
                year=item.get("year"),
                n_control=item.get("n_control"),
                n_treatment=item.get("n_treatment"),
                p_value_reported=item.get("p_value_reported"),
                effect_size_reported=item.get("effect_size_reported"),
                outcome_type=item.get("outcome_type"),
                test_type=item.get("test_type")
            )
            summaries.append(summary)
    
    # Load reconstructed results
    reconstructed_results = {}
    with open(args.reconstructed, 'r', encoding='utf-8') as f:
        reconstructed_results = json.load(f)
    
    # Validate
    records = validate_all_summaries(summaries, reconstructed_results)
    
    # Write report
    write_audit_report(records, Path(args.output))
    
    # Print summary
    total = len(records)
    inconsistent = sum(1 for r in records if r.is_inconsistent)
    excluded = sum(1 for r in records if r.data_quality_warning is not None)
    
    logger.info(f"Validation complete. Total: {total}, Inconsistent: {inconsistent}, Excluded from prevalence: {excluded}")
    
    return 0


if __name__ == "__main__":
    main()