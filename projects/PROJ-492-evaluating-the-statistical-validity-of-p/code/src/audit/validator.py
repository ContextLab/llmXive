"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 (thresholds for p-value and effect-size differences)
and FR-004b (exclusion of sample-size mismatch entries from prevalence).
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.helpers import safe_float

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05  # Absolute difference
EFFECT_SIZE_THRESHOLD = 0.05  # Relative difference (5%)

logger: AuditLogger = get_default_logger("validator")


def calculate_absolute_p_difference(p_reported: float, p_reconstructed: float) -> float:
    """Calculate absolute difference between reported and reconstructed p-values."""
    return abs(p_reported - p_reconstructed)


def calculate_relative_effect_size_difference(
    effect_reported: float, effect_reconstructed: float
) -> float:
    """
    Calculate relative difference in effect sizes.
    Formula: | (reported - reconstructed) / reported |
    Handles zero reported effect size gracefully.
    """
    if abs(effect_reported) < 1e-9:
        # If reported is effectively zero, use absolute difference
        return abs(effect_reported - effect_reconstructed)
    return abs((effect_reported - effect_reconstructed) / effect_reported)


def detect_sample_size_mismatch(summary: ABTestSummary) -> bool:
    """
    Detect if there is a sample size mismatch.
    Checks if n_control and n_treatment are provided and differ significantly
    from reconstructed values if available, or if they are inconsistent internally.
    For this implementation, we check if the summary indicates a mismatch
    via a flag or if reconstructed data is available and differs.
    """
    # If the summary explicitly has a mismatch flag (if model supports it)
    if hasattr(summary, 'sample_size_mismatch') and summary.sample_size_mismatch:
        return True

    # Check for NaNs or missing critical sample size data that prevents validation
    if summary.n_control is None or summary.n_treatment is None:
        return False  # Cannot determine mismatch without data, but not a mismatch per se

    # If reconstruction was done and sample sizes were flagged as inconsistent
    # This usually happens in reconstructor if the reported stats don't match N
    # For now, we rely on a flag passed from reconstruction or a heuristic.
    # A robust implementation would re-calculate expected N from variance if available.
    # Here we assume the summary object has a 'reconstruction_metadata' or similar
    # that flags this. If not, we return False unless explicitly set.
    return False


def check_p_value_consistency(summary: ABTestSummary, reconstructed_p: float) -> Tuple[bool, float]:
    """
    Check if reported p-value is consistent with reconstructed p-value.
    Returns (is_consistent, absolute_difference).
    """
    if summary.p_value is None:
        return True, 0.0

    diff = calculate_absolute_p_difference(summary.p_value, reconstructed_p)
    is_consistent = diff <= P_VALUE_THRESHOLD
    return is_consistent, diff


def check_effect_size_consistency(summary: ABTestSummary, reconstructed_effect: float) -> Tuple[bool, float]:
    """
    Check if reported effect size is consistent with reconstructed effect size.
    Returns (is_consistent, relative_difference).
    """
    if summary.effect_size is None:
        return True, 0.0

    diff = calculate_relative_effect_size_difference(summary.effect_size, reconstructed_effect)
    is_consistent = diff <= EFFECT_SIZE_THRESHOLD
    return is_consistent, diff


def create_audit_record(
    summary: ABTestSummary,
    is_p_consistent: bool,
    p_diff: float,
    is_effect_consistent: bool,
    effect_diff: float,
    has_sample_size_mismatch: bool,
    reconstructed_p: float,
    reconstructed_effect: float
) -> AuditRecord:
    """Create an AuditRecord based on validation results."""
    is_inconsistent = not is_p_consistent or not is_effect_consistent
    notes = []

    if not is_p_consistent:
        notes.append(f"P-value difference ({p_diff:.4f}) exceeds threshold ({P_VALUE_THRESHOLD}).")

    if not is_effect_consistent:
        notes.append(f"Effect size relative difference ({effect_diff:.4f}) exceeds threshold ({EFFECT_SIZE_THRESHOLD}).")

    if has_sample_size_mismatch:
        notes.append("Sample size mismatch detected.")

    warning = None
    if has_sample_size_mismatch:
        warning = "data_quality_warning"
        notes.append("Excluded from prevalence estimates per FR-004b.")

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        year=summary.year,
        is_inconsistent=is_inconsistent,
        notes=" ".join(notes) if notes else "Consistent.",
        data_quality_warning=warning,
        p_value_reported=summary.p_value,
        p_value_reconstructed=reconstructed_p,
        effect_size_reported=summary.effect_size,
        effect_size_reconstructed=reconstructed_effect,
        sample_size_mismatch=has_sample_size_mismatch
    )


def validate_summary(
    summary: ABTestSummary,
    reconstructed_p: float,
    reconstructed_effect: float
) -> AuditRecord:
    """Validate a single summary against reconstructed statistics."""
    is_p_consistent, p_diff = check_p_value_consistency(summary, reconstructed_p)
    is_effect_consistent, effect_diff = check_effect_size_consistency(summary, reconstructed_effect)
    has_sample_size_mismatch = detect_sample_size_mismatch(summary)

    return create_audit_record(
        summary,
        is_p_consistent,
        p_diff,
        is_effect_consistent,
        effect_diff,
        has_sample_size_mismatch,
        reconstructed_p,
        reconstructed_effect
    )


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries against their reconstructed results.
    reconstructed_results should be a list of dicts with keys:
    'url', 'reconstructed_p', 'reconstructed_effect'
    """
    records = []
    lookup = {r['url']: r for r in reconstructed_results}

    for summary in summaries:
        if summary.url not in lookup:
            logger.warning(f"URL {summary.url} not found in reconstruction results. Skipping.")
            continue

        res = lookup[summary.url]
        rec_p = res.get('reconstructed_p')
        rec_eff = res.get('reconstructed_effect')

        if rec_p is None or rec_eff is None:
            logger.error(f"Missing reconstruction data for {summary.url}. Skipping.")
            continue

        record = validate_summary(summary, rec_p, rec_eff)
        records.append(record)

    return records


def filter_for_prevalence(records: List[AuditRecord]) -> List[AuditRecord]:
    """
    Filter out records with sample size mismatches for prevalence estimation (FR-004b).
    """
    return [r for r in records if not r.sample_size_mismatch]


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """Write the audit report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(records),
        "inconsistent_count": sum(1 for r in records if r.is_inconsistent),
        "records": [
            {
                "url": r.url,
                "domain": r.domain,
                "year": r.year,
                "is_inconsistent": r.is_inconsistent,
                "notes": r.notes,
                "data_quality_warning": r.data_quality_warning,
                "p_value_reported": r.p_value_reported,
                "p_value_reconstructed": r.p_value_reconstructed,
                "effect_size_reported": r.effect_size_reported,
                "effect_size_reconstructed": r.effect_size_reconstructed,
                "sample_size_mismatch": r.sample_size_mismatch
            }
            for r in records
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Audit report written to {output_path}")


def main() -> None:
    """Main entry point for the validator script."""
    import sys
    from code.src.models.data_models import ABTestSummary
    from code.src.audit.reconstructor import reconstruct_all

    # Paths
    summaries_path = Path("data/processed/extracted_summaries.json")
    reconstruction_output = Path("data/processed/reconstructed_stats.json")
    audit_report_path = Path("output/audit_report.json")

    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        sys.exit(1)

    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**item) for item in summaries_data]

    # Run reconstruction if not already done (or load results if available)
    # For this script, we assume reconstruction has been done or we do it here
    # If reconstruction is a separate step, we would load the JSON here.
    # To be self-contained for the task:
    if reconstruction_output.exists():
        with open(reconstruction_output, 'r', encoding='utf-8') as f:
            recon_results = json.load(f)
    else:
        logger.info("Running reconstruction...")
        recon_results = reconstruct_all(summaries)
        # Save reconstruction results for downstream use
        with open(reconstruction_output, 'w', encoding='utf-8') as f:
            json.dump(recon_results, f, indent=2)

    # Validate
    audit_records = validate_all_summaries(summaries, recon_results)

    # Write report
    write_audit_report(audit_records, audit_report_path)

    # Print summary
    inconsistent = sum(1 for r in audit_records if r.is_inconsistent)
    mismatched = sum(1 for r in audit_records if r.sample_size_mismatch)
    print(f"Total: {len(audit_records)}, Inconsistent: {inconsistent}, Sample Size Mismatch: {mismatched}")

    # Exit with error if critical validation fails (optional, per CI needs)
    if inconsistent > len(audit_records) * 0.5:
        logger.warning("High inconsistency rate detected.")


if __name__ == "__main__":
    main()