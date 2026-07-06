"""
Validator module for A/B test summaries.
Implements FR-004 (inconsistency thresholds) and FR-004b (sample-size exclusion).
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message

logger = get_default_logger(__name__)

# FR-004 Thresholds
ABSOLUTE_P_DIFF_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

def calculate_absolute_p_difference(p_reported: Optional[float], p_reconstructed: Optional[float]) -> Optional[float]:
    """Calculate absolute difference between reported and reconstructed p-values."""
    if p_reported is None or p_reconstructed is None:
        return None
    return abs(p_reported - p_reconstructed)

def calculate_relative_effect_size_difference(
    effect_reported: Optional[float],
    effect_reconstructed: Optional[float]
) -> Optional[float]:
    """Calculate relative difference in effect sizes."""
    if effect_reported is None or effect_reconstructed is None:
        return None
    if abs(effect_reported) < 1e-9:
        return None  # Avoid division by zero
    return abs(effect_reported - effect_reconstructed) / abs(effect_reported)

def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if sample sizes in the summary are inconsistent or malformed.
    Returns True if a mismatch is detected.
    """
    if summary.n_control is None or summary.n_treatment is None:
        return True
    if summary.n_control <= 0 or summary.n_treatment <= 0:
        return True
    # Check for extremely skewed ratios that might indicate data entry errors
    ratio = max(summary.n_control, summary.n_treatment) / max(min(summary.n_control, summary.n_treatment), 1)
    if ratio > 100: # Arbitrary high threshold for obvious errors
        return True
    return False

def check_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[float]]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value_reconstructed is None or summary.p_value_reported is None:
        return True, None  # Cannot check if missing

    diff = calculate_absolute_p_difference(summary.p_value_reported, summary.p_value_reconstructed)
    if diff is None:
        return True, None

    is_consistent = diff <= ABSOLUTE_P_DIFF_THRESHOLD
    return is_consistent, diff

def check_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[float]]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size_reconstructed is None or summary.effect_size_reported is None:
        return True, None

    diff = calculate_relative_effect_size_difference(summary.effect_size_reported, summary.effect_size_reconstructed)
    if diff is None:
        return True, None

    is_consistent = diff <= RELATIVE_EFFECT_SIZE_THRESHOLD
    return is_consistent, diff

def create_audit_record(
    summary: ABTestSummary,
    p_consistent: bool,
    p_diff: Optional[float],
    effect_consistent: bool,
    effect_diff: Optional[float],
    has_sample_mismatch: bool
) -> AuditRecord:
    """Create an AuditRecord from validation results."""
    warnings = []
    inconsistencies = []

    if has_sample_mismatch:
        warnings.append(get_error_message("ERR-040", "Sample size mismatch detected"))
    
    if not p_consistent and p_diff is not None:
        inconsistencies.append(f"p-value diff: {p_diff:.4f} > {ABSOLUTE_P_DIFF_THRESHOLD}")
    
    if not effect_consistent and effect_diff is not None:
        inconsistencies.append(f"Effect size rel. diff: {effect_diff:.2%} > {RELATIVE_EFFECT_SIZE_THRESHOLD}")

    is_inconsistent = len(inconsistencies) > 0

    return AuditRecord(
        id=summary.id,
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        inconsistency_reasons=inconsistencies,
        data_quality_warnings=warnings,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=summary.p_value_reconstructed,
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=summary.effect_size_reconstructed,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        validated_at=datetime.utcnow().isoformat()
    )

def validate_summary(summary: ABTestSummary) -> AuditRecord:
    """Validate a single summary against FR-004 thresholds."""
    has_sample_mismatch = detect_sample_size_mismatch(summary)
    
    p_consistent, p_diff = check_p_value_consistency(summary)
    effect_consistent, effect_diff = check_effect_size_consistency(summary)

    return create_audit_record(
        summary, p_consistent, p_diff, effect_consistent, effect_diff, has_sample_mismatch
    )

def validate_all_summaries(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """Validate a list of summaries."""
    records = []
    for summary in summaries:
        try:
            record = validate_summary(summary)
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to validate summary {summary.id}: {e}")
            # Create a failure record
            records.append(AuditRecord(
                id=summary.id,
                url=summary.url,
                domain=summary.domain,
                year=summary.year,
                is_inconsistent=True,
                inconsistency_reasons=[f"Validation error: {str(e)}"],
                data_quality_warnings=[],
                validated_at=datetime.utcnow().isoformat()
            ))
    return records

def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    FR-004b: Filter out records with sample-size mismatches from prevalence estimates.
    """
    return [r for r in records if not any("Sample size mismatch" in w for w in r.data_quality_warnings)]

def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write audit records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = [record.model_dump() for record in records]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Audit report written to {output_path}")

def main() -> int:
    """Main entry point for running the validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries")
    parser.add_argument("--input", type=str, required=True, help="Path to input summaries JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output audit report JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    # Load summaries
    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**data) for data in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")

    # Validate
    records = validate_all_summaries(summaries)
    logger.info(f"Validated {len(records)} summaries")

    # Write report
    write_audit_report(records, output_path)

    # Count inconsistencies
    inconsistent_count = sum(1 for r in records if r.is_inconsistent)
    logger.info(f"Inconsistent summaries: {inconsistent_count}/{len(records)}")

    # Count sample size mismatches
    mismatch_count = sum(1 for r in records if any("Sample size mismatch" in w for w in r.data_quality_warnings))
    logger.info(f"Sample size mismatches: {mismatch_count}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
