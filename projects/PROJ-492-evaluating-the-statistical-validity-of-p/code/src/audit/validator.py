"""
Inconsistency Validator for A/B Test Summaries.

Implements FR-004 thresholds:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%

Implements FR-004b:
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects with data_quality_warning for discrepancies.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED, set_rng_seed

# Thresholds per FR-004
THRESHOLD_P_ABSOLUTE = 0.05
THRESHOLD_EFFECT_RELATIVE = 0.05  # 5%

logger = get_default_logger(__name__)


def calculate_relative_difference(value_a: float, value_b: float) -> float:
    """
    Calculate relative difference between two values.
    Returns (|a - b|) / max(|a|, |b|, epsilon).
    Handles zero cases safely.
    """
    if value_a == 0 and value_b == 0:
        return 0.0
    denominator = max(abs(value_a), abs(value_b), 1e-9)
    return abs(value_a - value_b) / denominator


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_p_value: float,
    reconstructed_effect_size: float,
    reconstructed_sample_size: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[str], bool]:
    """
    Validate a single summary against reconstructed values.

    Returns:
        (is_consistent, p_diff_reason, effect_diff_reason, has_sample_size_warning)
    """
    issues = []
    has_sample_size_warning = False

    # 1. Check Sample Size Mismatch (FR-004b)
    if summary.sample_size is not None and reconstructed_sample_size is not None:
        if summary.sample_size != reconstructed_sample_size:
            has_sample_size_warning = True
            # Note: We flag it, but we do NOT exclude it from the record itself,
            # only from aggregate prevalence estimates later.
            # The task says "exclude from aggregate prevalence estimates",
            # implying the record exists but is marked or filtered for aggregation.
            # We will generate the warning in the AuditRecord.

    # 2. Check P-value consistency (FR-004)
    if summary.p_value is not None and reconstructed_p_value is not None:
        abs_diff = abs(summary.p_value - reconstructed_p_value)
        if abs_diff > THRESHOLD_P_ABSOLUTE:
            reason = f"P-value discrepancy: reported={summary.p_value:.4f}, reconstructed={reconstructed_p_value:.4f}, diff={abs_diff:.4f} > {THRESHOLD_P_ABSOLUTE}"
            issues.append(reason)

    # 3. Check Effect Size consistency (FR-004)
    if summary.effect_size is not None and reconstructed_effect_size is not None:
        rel_diff = calculate_relative_difference(summary.effect_size, reconstructed_effect_size)
        if rel_diff > THRESHOLD_EFFECT_RELATIVE:
            reason = f"Effect size discrepancy: reported={summary.effect_size:.4f}, reconstructed={reconstructed_effect_size:.4f}, rel_diff={rel_diff:.2%} > {THRESHOLD_EFFECT_RELATIVE}"
            issues.append(reason)

    is_consistent = len(issues) == 0
    p_diff_reason = issues[0] if (len(issues) > 0 and "P-value" in issues[0]) else None
    effect_diff_reason = issues[0] if (len(issues) > 0 and "Effect size" in issues[0]) else None

    # If only sample size mismatch exists, is_consistent is True regarding statistical thresholds,
    # but we still need to flag it in the record.
    # However, usually "inconsistent" implies failing the statistical thresholds.
    # We will treat statistical thresholds as the primary consistency check.
    # But we must include the warning in the output.

    return is_consistent, p_diff_reason, effect_diff_reason, has_sample_size_warning


def run_validator(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]],
    output_path: Path
) -> List[AuditRecord]:
    """
    Run validation on all summaries and generate AuditRecords.

    Args:
        summaries: List of extracted ABTestSummary objects.
        reconstructed_results: List of dicts containing reconstruction results
                             (keys: 'summary_id', 'p_value', 'effect_size', 'sample_size').
        output_path: Path to write the audit_report.json.

    Returns:
        List of AuditRecord objects.
    """
    # Map reconstructed results by ID for quick lookup
    recon_map = {r['summary_id']: r for r in reconstructed_results}

    audit_records = []
    timestamp = datetime.utcnow().isoformat() + "Z"

    for summary in summaries:
        recon = recon_map.get(summary.id)
        if not recon:
            logger.warning(f"No reconstruction found for {summary.id}. Skipping.")
            continue

        reconstructed_p = recon.get('p_value')
        reconstructed_effect = recon.get('effect_size')
        reconstructed_n = recon.get('sample_size')

        is_consistent, p_reason, effect_reason, has_n_warning = validate_single_summary(
            summary, reconstructed_p, reconstructed_effect, reconstructed_n
        )

        notes = []
        if p_reason:
            notes.append(p_reason)
        if effect_reason:
            notes.append(effect_reason)
        if has_n_warning:
            notes.append("data_quality_warning: Sample size mismatch detected.")

        # Determine flags
        flags = []
        if p_reason:
            flags.append("p_value_mismatch")
        if effect_reason:
            flags.append("effect_size_mismatch")
        if has_n_warning:
            flags.append("sample_size_mismatch")

        record = AuditRecord(
            summary_id=summary.id,
            url=summary.url,
            domain=summary.domain,
            is_consistent=is_consistent and not has_n_warning, # If sample size mismatch, mark inconsistent for aggregation logic?
            # Per FR-004b: "exclude sample-size mismatch entries from aggregate prevalence estimates".
            # We will handle the exclusion logic in the prevalence module or here if needed.
            # For the record itself, we flag it.
            # Let's set is_consistent to False if there are ANY issues including sample size mismatch
            # to ensure it's excluded from "consistent" counts in downstream aggregations unless specified otherwise.
            # Re-reading: "exclude ... from aggregate prevalence estimates".
            # We will add a specific field `exclude_from_prevalence` to handle this explicitly.
            
            flags=flags,
            notes="; ".join(notes) if notes else None,
            timestamp=timestamp,
            extracted_p=summary.p_value,
            reconstructed_p=reconstructed_p,
            extracted_effect=summary.effect_size,
            reconstructed_effect=reconstructed_effect,
            extracted_n=summary.sample_size,
            reconstructed_n=reconstructed_n,
            exclude_from_prevalence=has_n_warning
        )
        audit_records.append(record)

    # Write to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        # Convert dataclasses to dicts
        records_dicts = [r.model_dump() if hasattr(r, 'model_dump') else r.__dict__ for r in audit_records]
        json.dump(records_dicts, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path} with {len(audit_records)} records.")
    return audit_records


def main():
    """Entry point for validator script."""
    # Set seed for reproducibility if needed
    set_rng_seed(SEED)

    # Paths
    base_dir = Path(__file__).resolve().parents[2]
    summaries_path = base_dir / "data" / "extracted" / "summaries.json"
    reconstructions_path = base_dir / "data" / "processed" / "reconstruction_results.json"
    output_path = base_dir / "output" / "audit_report.json"

    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return 1

    if not reconstructions_path.exists():
        logger.error(f"Reconstruction results file not found: {reconstructions_path}")
        return 1

    # Load data
    with open(summaries_path, 'r') as f:
        summaries_data = json.load(f)
    
    # Convert to ABTestSummary objects (assuming list of dicts)
    # We need to handle the case where the JSON is a list of dicts
    summaries = []
    for item in summaries_data:
        # Create ABTestSummary from dict
        try:
            summaries.append(ABTestSummary(**item))
        except Exception as e:
            logger.warning(f"Skipping invalid summary item: {e}")
            continue

    with open(reconstructions_path, 'r') as f:
        recon_data = json.load(f)

    # Run validator
    records = run_validator(summaries, recon_data, output_path)

    # Print summary
    total = len(records)
    consistent = sum(1 for r in records if r.is_consistent)
    excluded = sum(1 for r in records if r.exclude_from_prevalence)
    
    logger.info(f"Validation complete. Total: {total}, Consistent: {consistent}, Excluded from prevalence: {excluded}")

    return 0


if __name__ == "__main__":
    exit(main())
