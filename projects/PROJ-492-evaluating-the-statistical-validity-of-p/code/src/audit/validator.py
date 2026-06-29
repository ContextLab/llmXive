"""
Inconsistency Validator for A/B Test Audit Pipeline.

Implements FR-004 thresholds:
- Absolute p-difference > 0.05 flags inconsistency
- Relative effect-size > 5% flags inconsistency
- Sample-size mismatches are flagged with data_quality_warning
  and excluded from aggregate prevalence estimates (FR-004b)

Generates AuditRecord objects and writes output/audit_report.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import safe_float
from code.src.config import get_config_summary

# Threshold constants per FR-004
P_VALUE_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

# Sample size mismatch tolerance (10% relative difference)
SAMPLE_SIZE_TOLERANCE = 0.10

logger = get_default_logger(__name__)


def calculate_absolute_p_difference(
    reported_p_value: Optional[float],
    reconstructed_p_value: Optional[float]
) -> Optional[float]:
    """
    Calculate absolute difference between reported and reconstructed p-values.

    Args:
        reported_p_value: P-value reported in the original summary
        reconstructed_p_value: P-value reconstructed from raw metrics

    Returns:
        Absolute difference or None if either value is missing
    """
    if reported_p_value is None or reconstructed_p_value is None:
        return None
    return abs(reported_p_value - reconstructed_p_value)


def calculate_relative_effect_size_difference(
    reported_effect_size: Optional[float],
    reconstructed_effect_size: Optional[float]
) -> Optional[float]:
    """
    Calculate relative difference in effect sizes.

    Args:
        reported_effect_size: Effect size reported in original summary
        reconstructed_effect_size: Effect size reconstructed from raw metrics

    Returns:
        Relative difference (|reported - reconstructed| / |reported|) or None
    """
    if reported_effect_size is None or reconstructed_effect_size is None:
        return None
    if abs(reported_effect_size) < 1e-10:
        # Avoid division by zero for near-zero effect sizes
        return None
    return abs(reported_effect_size - reconstructed_effect_size) / abs(reported_effect_size)


def detect_sample_size_mismatch(
    summary: ABTestSummary
) -> Tuple[bool, Optional[str]]:
    """
    Detect if sample sizes in the summary are inconsistent or missing.

    Per FR-004b, entries with sample-size mismatches should be flagged
    with data_quality_warning and excluded from aggregate prevalence estimates.

    Args:
        summary: ABTestSummary object with sample size fields

    Returns:
        Tuple of (is_mismatch, warning_message)
    """
    n_control = safe_float(summary.n_control)
    n_treatment = safe_float(summary.n_treatment)

    # Check for missing sample sizes
    if n_control is None or n_treatment is None:
        return True, "ERR-045: Missing sample size data"

    # Check for zero sample sizes
    if n_control <= 0 or n_treatment <= 0:
        return True, "ERR-046: Invalid sample size (zero or negative)"

    # Check for large relative difference between sample sizes
    # This detects when reported sample sizes seem inconsistent
    avg_size = (n_control + n_treatment) / 2
    if avg_size > 0:
        relative_diff = abs(n_control - n_treatment) / avg_size
        if relative_diff > SAMPLE_SIZE_TOLERANCE:
            return True, f"ERR-047: Sample size mismatch ({n_control} vs {n_treatment})"

    return False, None


def check_p_value_consistency(
    summary: ABTestSummary,
    reconstructed_p_value: float
) -> Tuple[bool, Optional[float], str]:
    """
    Check if reported p-value is consistent with reconstructed p-value.

    Args:
        summary: ABTestSummary with reported p-value
        reconstructed_p_value: P-value from statistical reconstruction

    Returns:
        Tuple of (is_inconsistent, p_difference, error_code)
    """
    reported_p = safe_float(summary.p_value)

    if reported_p is None:
        return False, None, "ERR-048: Missing reported p-value"

    p_diff = calculate_absolute_p_difference(reported_p, reconstructed_p_value)

    if p_diff is None:
        return False, None, "ERR-048: Could not calculate p-value difference"

    if p_diff > P_VALUE_DIFF_THRESHOLD:
        return True, p_diff, "ERR-049: P-value inconsistency detected"

    return False, p_diff, "OK"


def check_effect_size_consistency(
    summary: ABTestSummary,
    reconstructed_effect_size: Optional[float]
) -> Tuple[bool, Optional[float], str]:
    """
    Check if reported effect size is consistent with reconstructed effect size.

    Args:
        summary: ABTestSummary with reported effect size
        reconstructed_effect_size: Effect size from reconstruction

    Returns:
        Tuple of (is_inconsistent, effect_size_diff, error_code)
    """
    reported_effect = safe_float(summary.effect_size)

    if reported_effect is None or reconstructed_effect_size is None:
        return False, None, "ERR-050: Missing effect size data"

    effect_diff = calculate_relative_effect_size_difference(
        reported_effect, reconstructed_effect_size
    )

    if effect_diff is None:
        return False, None, "ERR-050: Could not calculate effect size difference"

    if effect_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
        return True, effect_diff, "ERR-051: Effect size inconsistency detected"

    return False, effect_diff, "OK"


def create_audit_record(
    summary: ABTestSummary,
    reconstructed_p_value: Optional[float],
    reconstructed_effect_size: Optional[float],
    p_inconsistent: bool,
    p_difference: Optional[float],
    effect_inconsistent: bool,
    effect_difference: Optional[float],
    sample_size_warning: Optional[str]
) -> AuditRecord:
    """
    Create an AuditRecord from validation results.

    Args:
        summary: Original ABTestSummary
        reconstructed_p_value: Reconstructed p-value
        reconstructed_effect_size: Reconstructed effect size
        p_inconsistent: Whether p-value is inconsistent
        p_difference: Absolute p-value difference
        effect_inconsistent: Whether effect size is inconsistent
        effect_difference: Relative effect size difference
        sample_size_warning: Warning message if sample size mismatch

    Returns:
        AuditRecord with validation results
    """
    audit_notes = []

    if sample_size_warning:
        audit_notes.append(sample_size_warning)
    if p_inconsistent:
        audit_notes.append(f"P-value difference: {p_difference:.4f}")
    if effect_inconsistent:
        audit_notes.append(f"Effect size difference: {effect_difference:.4f}")

    notes_str = "; ".join(audit_notes) if audit_notes else "No inconsistencies detected"

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        source_id=summary.source_id,
        extraction_timestamp=summary.extraction_timestamp,
        reconstructed_p_value=reconstructed_p_value,
        reconstructed_effect_size=reconstructed_effect_size,
        reported_p_value=summary.p_value,
        reported_effect_size=summary.effect_size,
        n_control=summary.n_control,
        n_treatment=summary.n_treatment,
        is_p_value_inconsistent=p_inconsistent,
        is_effect_size_inconsistent=effect_inconsistent,
        is_inconsistent=p_inconsistent or effect_inconsistent,
        data_quality_warning=sample_size_warning is not None,
        audit_notes=notes_str,
        validation_timestamp=datetime.utcnow().isoformat()
    )


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p_value: Optional[float],
    reconstructed_effect_size: Optional[float] = None
) -> AuditRecord:
    """
    Validate a single ABTestSummary against statistical reconstruction.

    Per FR-004:
    - Absolute p-difference > 0.05 flags inconsistency
    - Relative effect-size > 5% flags inconsistency

    Per FR-004b:
    - Sample-size mismatch entries get data_quality_warning
    - These entries are excluded from aggregate prevalence estimates

    Args:
        summary: ABTestSummary to validate
        reconstructed_p_value: Reconstructed p-value from T023
        reconstructed_effect_size: Reconstructed effect size (optional)

    Returns:
        AuditRecord with validation results
    """
    logger.info(f"Validating summary for URL: {summary.url}")

    # Check sample size consistency (FR-004b)
    has_sample_size_mismatch, sample_size_warning = detect_sample_size_mismatch(summary)

    # Check p-value consistency (FR-004)
    p_inconsistent, p_difference, p_error = check_p_value_consistency(
        summary, reconstructed_p_value or 0.0
    )

    # Check effect size consistency (FR-004)
    effect_inconsistent, effect_difference, effect_error = check_effect_size_consistency(
        summary, reconstructed_effect_size
    )

    # Create audit record
    audit_record = create_audit_record(
        summary=summary,
        reconstructed_p_value=reconstructed_p_value,
        reconstructed_effect_size=reconstructed_effect_size,
        p_inconsistent=p_inconsistent,
        p_difference=p_difference,
        effect_inconsistent=effect_inconsistent,
        effect_difference=effect_difference,
        sample_size_warning=sample_size_warning
    )

    return audit_record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: Dict[str, Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate multiple ABTestSummaries against reconstructed results.

    Args:
        summaries: List of ABTestSummary objects
        reconstructed_results: Dict mapping URL to reconstruction results
            with keys 'p_value' and optionally 'effect_size'

    Returns:
        List of AuditRecord objects
    """
    audit_records = []

    for summary in summaries:
        url = summary.url
        recon = reconstructed_results.get(url, {})

        recon_p = recon.get('p_value')
        recon_effect = recon.get('effect_size')

        audit_record = validate_summary(
            summary=summary,
            reconstructed_p_value=recon_p,
            reconstructed_effect_size=recon_effect
        )
        audit_records.append(audit_record)

    return audit_records


def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> Path:
    """
    Write audit records to JSON file.

    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file

    Returns:
        Path to written file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    records_data = [record.model_dump(mode='json') for record in audit_records]

    report = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "config_summary": get_config_summary(),
            "thresholds": {
                "p_value_diff_threshold": P_VALUE_DIFF_THRESHOLD,
                "effect_size_relative_threshold": EFFECT_SIZE_RELATIVE_THRESHOLD,
                "sample_size_tolerance": SAMPLE_SIZE_TOLERANCE
            }
        },
        "records": records_data,
        "summary": {
            "total_records": len(audit_records),
            "inconsistent_count": sum(1 for r in audit_records if r.is_inconsistent),
            "data_quality_warnings": sum(1 for r in audit_records if r.data_quality_warning),
            "p_value_inconsistencies": sum(1 for r in audit_records if r.is_p_value_inconsistent),
            "effect_size_inconsistencies": sum(1 for r in audit_records if r.is_effect_size_inconsistent)
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path}")
    return output_path


def filter_for_prevalence(
    audit_records: List[AuditRecord]
) -> List[AuditRecord]:
    """
    Filter audit records to exclude those with data quality warnings.

    Per FR-004b, entries flagged for sample-size mismatch must be excluded
    from aggregate prevalence estimates.

    Args:
        audit_records: List of all AuditRecord objects

    Returns:
        List of AuditRecord objects suitable for prevalence calculation
    """
    return [r for r in audit_records if not r.data_quality_warning]


def main():
    """
    Main entry point for standalone validator execution.

    Reads reconstructed results from data/reconstruction_results.json
    and summaries from output/extracted_summaries.json
    Writes audit report to output/audit_report.json
    """
    logger.info("Starting inconsistency validation")

    # Paths
    summaries_path = Path("output/extracted_summaries.json")
    reconstructions_path = Path("data/reconstruction_results.json")
    output_path = Path("output/audit_report.json")

    # Load summaries
    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return 1

    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary.model_validate(s) for s in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")

    # Load reconstructed results
    reconstructed_results = {}
    if reconstructions_path.exists():
        with open(reconstructions_path, 'r', encoding='utf-8') as f:
            reconstructed_results = json.load(f)
        logger.info(f"Loaded reconstruction results for {len(reconstructed_results)} URLs")
    else:
        logger.warning(f"Reconstruction results not found: {reconstructions_path}")

    # Validate all summaries
    audit_records = validate_all_summaries(summaries, reconstructed_results)
    logger.info(f"Validated {len(audit_records)} summaries")

    # Write audit report
    write_audit_report(audit_records, output_path)

    # Print summary
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    warnings = sum(1 for r in audit_records if r.data_quality_warning)
    logger.info(f"Validation complete: {inconsistent} inconsistent, {warnings} data quality warnings")

    return 0


if __name__ == "__main__":
    exit(main())
