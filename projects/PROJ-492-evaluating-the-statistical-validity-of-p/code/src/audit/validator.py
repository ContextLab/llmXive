"""
Inconsistency Validator for A/B Test Summaries.

Applies FR-004 thresholds to detect statistical inconsistencies between
reported and reconstructed metrics, and handles sample-size mismatches
per FR-004b.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED
import numpy as np

# Constants for FR-004 thresholds
ABSOLUTE_P_DIFFERENCE_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

def validate_single_summary(
    summary: ABTestSummary,
    reconstructed_p_value: float,
    reconstructed_effect_size: float,
    logger: AuditLogger
) -> AuditRecord:
    """
    Validate a single summary against reconstructed metrics.

    Returns an AuditRecord with flags for inconsistency and data quality warnings.
    """
    inconsistencies = []
    warnings = []
    is_inconsistent = False

    # Check for sample size mismatch (FR-004b)
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        # Assuming reconstructed data has matching sample sizes or we check against summary
        # If the reconstructor flagged a mismatch, it should be in the summary or passed here.
        # For this implementation, we assume the summary contains the raw data and we check
        # if the summary itself has conflicting sample size info or if the reconstruction
        # failed due to it.
        # Based on task description: "generate AuditRecord objects with data_quality_warning
        # messages for sample-size discrepancies".
        # We assume the 'summary' object might have a flag or we check internal consistency.
        # If the reconstructor couldn't compute a valid effect size due to mismatch,
        # we flag it.
        if reconstructed_effect_size is None or np.isnan(reconstructed_effect_size):
            warnings.append("Sample size mismatch detected; effect size could not be reliably computed.")
            is_inconsistent = True # Flagged as problematic
        elif summary.sample_size_control <= 0 or summary.sample_size_treatment <= 0:
             warnings.append("Invalid sample size (<= 0) detected.")
             is_inconsistent = True

    # Check absolute p-value difference (FR-004)
    reported_p_value = summary.p_value
    if reported_p_value is not None and reconstructed_p_value is not None:
        p_diff = abs(reported_p_value - reconstructed_p_value)
        if p_diff > ABSOLUTE_P_DIFFERENCE_THRESHOLD:
            inconsistencies.append({
                "type": "p_value_mismatch",
                "reported": reported_p_value,
                "reconstructed": reconstructed_p_value,
                "difference": p_diff,
                "threshold": ABSOLUTE_P_DIFFERENCE_THRESHOLD
            })
            is_inconsistent = True

    # Check relative effect size difference (FR-004)
    reported_effect_size = summary.effect_size
    if reported_effect_size is not None and reconstructed_effect_size is not None and reported_effect_size != 0:
        # Relative difference: |reconstructed - reported| / |reported|
        rel_diff = abs(reconstructed_effect_size - reported_effect_size) / abs(reported_effect_size)
        if rel_diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
            inconsistencies.append({
                "type": "effect_size_mismatch",
                "reported": reported_effect_size,
                "reconstructed": reconstructed_effect_size,
                "relative_difference": rel_diff,
                "threshold": RELATIVE_EFFECT_SIZE_THRESHOLD
            })
            is_inconsistent = True

    # Construct the AuditRecord
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        is_inconsistent=is_inconsistent,
        inconsistencies=inconsistencies,
        data_quality_warnings=warnings,
        reconstructed_p_value=reconstructed_p_value,
        reconstructed_effect_size=reconstructed_effect_size,
        reported_p_value=reported_p_value,
        reported_effect_size=reported_effect_size,
        timestamp=datetime.utcnow().isoformat(),
        source_file=summary.source_file if hasattr(summary, 'source_file') else None
    )

    if is_inconsistent:
        logger.log_warning(
            f"Validation failed for {summary.url}: {len(inconsistencies)} inconsistencies found. Warnings: {warnings}",
            error_code="ERR-004"
        )
    elif warnings:
        logger.log_warning(
            f"Validation completed with warnings for {summary.url}: {warnings}",
            error_code="ERR-005"
        )

    return audit_record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: Dict[str, Dict[str, float]],
    output_path: Path
) -> List[AuditRecord]:
    """
    Validate a list of summaries against reconstructed results.

    Args:
        summaries: List of ABTestSummary objects.
        reconstructed_results: Dict mapping url -> {"p_value": float, "effect_size": float}
        output_path: Path to write the audit_report.json.

    Returns:
        List of AuditRecord objects.
    """
    logger = get_default_logger()
    audit_records = []

    for summary in summaries:
        url = summary.url
        recon = reconstructed_results.get(url, {})
        recon_p = recon.get("p_value")
        recon_eff = recon.get("effect_size")

        record = validate_single_summary(summary, recon_p, recon_eff, logger)
        audit_records.append(record)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write audit_report.json
    records_data = []
    for rec in audit_records:
        # Convert to dict, handling potential non-serializable types if any
        record_dict = rec.model_dump()
        records_data.append(record_dict)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2)

    logger.info(f"Audit report written to {output_path}")
    return audit_records


def run_validator(
    summaries_path: Path,
    reconstructor_output_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Main entry point to run the validator.

    Loads summaries and reconstructed results, validates, and writes report.
    """
    logger = get_default_logger()

    if not summaries_path.exists():
        logger.log_error(f"Summaries file not found: {summaries_path}", "ERR-001")
        raise FileNotFoundError(f"Summaries file not found: {summaries_path}")

    if not reconstructor_output_path.exists():
        logger.log_error(f"Reconstructor output file not found: {reconstructor_output_path}", "ERR-002")
        raise FileNotFoundError(f"Reconstructor output file not found: {reconstructor_output_path}")

    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**item) for item in summaries_data]

    # Load reconstructed results
    with open(reconstructor_output_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)

    # Validate
    audit_records = validate_all_summaries(summaries, reconstructed_data, output_path)

    return audit_records


def main():
    """CLI entry point for the validator."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Validate A/B test summaries against reconstructed metrics.")
    parser.add_argument("--summaries", type=str, required=True, help="Path to extracted summaries JSON")
    parser.add_argument("--reconstructed", type=str, required=True, help="Path to reconstructed metrics JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to write audit_report.json")

    args = parser.parse_args()

    try:
        run_validator(
            summaries_path=Path(args.summaries),
            reconstructor_output_path=Path(args.reconstructed),
            output_path=Path(args.output)
        )
        print(f"Validation complete. Report written to {args.output}")
    except Exception as e:
        logging.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
