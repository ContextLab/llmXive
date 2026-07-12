"""
Inconsistency Validator Module (T025).

Implements FR-004 and FR-004b:
- Validates statistical consistency between reported and reconstructed metrics.
- Applies thresholds: absolute p-difference > 0.05, relative effect-size > 5%.
- Flags sample-size mismatches with data_quality_warning.
- Excludes sample-size mismatch entries from aggregate prevalence estimates.
- Generates AuditRecord objects and writes output/audit_report.json.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05

logger = get_default_logger(__name__)


def calculate_relative_effect_size_diff(
    reported_effect: Optional[float],
    reconstructed_effect: Optional[float]
) -> Optional[float]:
    """
    Calculate the relative difference between reported and reconstructed effect sizes.
    Formula: |reported - reconstructed| / |reported|
    Returns None if reported effect is 0 or missing.
    """
    if reported_effect is None or reconstructed_effect is None:
        return None
    if abs(reported_effect) < 1e-9:
        return None  # Avoid division by zero
    return abs(reported_effect - reconstructed_effect) / abs(reported_effect)


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single A/B test summary against reconstructed values.
    Returns an AuditRecord with flags and warnings.
    """
    issues = []
    warnings = []
    is_inconsistent = False
    is_excluded = False

    # Check for sample size mismatch (FR-004b)
    sample_size_mismatch = False
    if summary.n_control is not None and reconstructed.get("n_control") is not None:
        if summary.n_control != reconstructed["n_control"]:
            sample_size_mismatch = True
            warnings.append(
                f"Sample size mismatch: reported={summary.n_control}, "
                f"reconstructed={reconstructed['n_control']}"
            )
            is_excluded = True

    if summary.n_treatment is not None and reconstructed.get("n_treatment") is not None:
        if summary.n_treatment != reconstructed["n_treatment"]:
            sample_size_mismatch = True
            warnings.append(
                f"Sample size mismatch: reported={summary.n_treatment}, "
                f"reconstructed={reconstructed['n_treatment']}"
            )
            is_excluded = True

    if sample_size_mismatch:
        # If sample sizes mismatch, we flag it and exclude from prevalence,
        # but we still record the audit.
        is_inconsistent = True  # Considered inconsistent due to data quality issue
        # We don't necessarily flag p-value inconsistency if we can't trust the N,
        # but the task says generate AuditRecord with data_quality_warning.
        # We will still check p-values if available, but the primary flag is the warning.

    # Check P-value consistency (FR-004)
    reported_p = summary.p_value
    reconstructed_p = reconstructed.get("p_value")

    if reported_p is not None and reconstructed_p is not None:
        p_diff = abs(reported_p - reconstructed_p)
        if p_diff > P_VALUE_THRESHOLD:
            is_inconsistent = True
            issues.append(
                f"P-value difference exceeds threshold: "
                f"|{reported_p:.4f} - {reconstructed_p:.4f}| = {p_diff:.4f} > {P_VALUE_THRESHOLD}"
            )

    # Check Effect Size consistency (FR-004)
    reported_effect = summary.effect_size
    reconstructed_effect = reconstructed.get("effect_size")

    if reported_effect is not None and reconstructed_effect is not None:
        rel_diff = calculate_relative_effect_size_diff(reported_effect, reconstructed_effect)
        if rel_diff is not None and rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            is_inconsistent = True
            issues.append(
                f"Relative effect size difference exceeds threshold: "
                f"{rel_diff:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}"
            )

    # Determine final status
    status = "inconsistent" if is_inconsistent else "consistent"
    if is_excluded:
        status = "inconsistent_excluded"

    # Construct AuditRecord
    record = AuditRecord(
        id=summary.id,
        url=summary.url,
        domain=summary.domain,
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect,
        reconstructed_effect_size=reconstructed_effect,
        sample_size_mismatch=sample_size_mismatch,
        is_inconsistent=is_inconsistent,
        is_excluded_from_prevalence=is_excluded,
        issues=issues,
        warnings=warnings,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

    return record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate a list of summaries against their reconstructed results.
    """
    if len(summaries) != len(reconstructed_results):
        raise ValueError(
            f"Mismatch in number of summaries ({len(summaries)}) "
            f"and reconstructed results ({len(reconstructed_results)})"
        )

    records = []
    for summary, recon in zip(summaries, reconstructed_results):
        record = validate_single_summary(summary, recon)
        records.append(record)
        if record.is_excluded_from_prevalence:
            logger.warning(
                f"Record {record.id} excluded from prevalence due to sample size mismatch"
            )
        elif record.is_inconsistent:
            logger.info(f"Record {record.id} flagged as inconsistent")
        else:
            logger.debug(f"Record {record.id} is consistent")

    return records


def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """
    Write the list of AuditRecord objects to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert AuditRecord objects to dictionaries for JSON serialization
    report_data = [record.model_dump() for record in records]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Audit report written to {output_path}")


def run_validator(
    summaries_path: Path,
    reconstructed_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Main entry point to run the validator.
    Loads summaries and reconstructed results, validates, and writes report.
    """
    # Load summaries
    with open(summaries_path, "r", encoding="utf-8") as f:
        summaries_data = json.load(f)
    summaries = [ABTestSummary(**item) for item in summaries_data]

    # Load reconstructed results
    with open(reconstructed_path, "r", encoding="utf-8") as f:
        reconstructed_data = json.load(f)

    # Validate
    records = validate_all_summaries(summaries, reconstructed_data)

    # Write report
    write_audit_report(records, output_path)

    return records


def main() -> int:
    """
    CLI entry point for the validator.
    Expects arguments: --summaries <path> --reconstructed <path> --output <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate A/B test summaries against reconstructed results.")
    parser.add_argument("--summaries", type=Path, required=True, help="Path to extracted summaries JSON")
    parser.add_argument("--reconstructed", type=Path, required=True, help="Path to reconstructed results JSON")
    parser.add_argument("--output", type=Path, required=True, help="Path to output audit report JSON")

    args = parser.parse_args()

    try:
        records = run_validator(args.summaries, args.reconstructed, args.output)
        inconsistent_count = sum(1 for r in records if r.is_inconsistent)
        excluded_count = sum(1 for r in records if r.is_excluded_from_prevalence)
        logger.info(
            f"Validation complete: {len(records)} records. "
            f"Inconsistent: {inconsistent_count}, Excluded: {excluded_count}"
        )
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
