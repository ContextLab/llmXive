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

# Thresholds from FR-004
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

logger = get_default_logger(__name__)

def check_sample_size_mismatch(summary: ABTestSummary) -> Tuple[bool, Optional[str]]:
    """
    Check if sample sizes for control and treatment are consistent.
    Returns (is_mismatch, warning_message).
    """
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        return False, None

    n_control = summary.sample_size_control
    n_treatment = summary.sample_size_treatment

    # Simple heuristic: if they differ by more than 10% (or absolute difference > 5)
    # we flag it as a potential data quality issue.
    # The exact threshold for "mismatch" is not strictly defined in FR-004b,
    # but we assume a significant discrepancy (e.g., > 20% difference) warrants a warning.
    if n_control > 0 and n_treatment > 0:
        ratio = n_treatment / n_control
        if ratio < 0.8 or ratio > 1.2:
            msg = f"Sample size mismatch detected: control={n_control}, treatment={n_treatment} (ratio={ratio:.2f})"
            return True, msg

    return False, None

def validate_p_value_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[float]]:
    """
    Check if the reported p-value is consistent with the reconstructed p-value.
    Returns (is_inconsistent, p_diff).
    """
    if summary.reconstructed_p_value is None or summary.reported_p_value is None:
        return False, None

    p_reported = summary.reported_p_value
    p_reconstructed = summary.reconstructed_p_value

    p_diff = abs(p_reported - p_reconstructed)
    if p_diff > P_VALUE_THRESHOLD:
        return True, p_diff

    return False, None

def validate_effect_size_consistency(summary: ABTestSummary) -> Tuple[bool, Optional[float]]:
    """
    Check if the reported effect size is consistent with the reconstructed effect size.
    Returns (is_inconsistent, rel_diff).
    """
    if summary.reconstructed_effect_size is None or summary.reported_effect_size is None:
        return False, None

    eff_reported = summary.reported_effect_size
    eff_reconstructed = summary.reconstructed_effect_size

    # Avoid division by zero
    if abs(eff_reconstructed) < 1e-9:
        if abs(eff_reported) > 1e-9:
            return True, float('inf')
        return False, None

    rel_diff = abs(eff_reported - eff_reconstructed) / abs(eff_reconstructed)
    if rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
        return True, rel_diff

    return False, None

def validate_single_summary(summary: ABTestSummary) -> AuditRecord:
    """
    Validate a single ABTestSummary and produce an AuditRecord.
    """
    is_inconsistent = False
    warnings = []
    reasons = []

    # Check sample size mismatch (FR-004b)
    has_mismatch, mismatch_msg = check_sample_size_mismatch(summary)
    if has_mismatch:
        warnings.append(mismatch_msg)
        # FR-004b: Mark for exclusion from prevalence, but still record
        reasons.append("SAMPLE_SIZE_MISMATCH")

    # Check p-value consistency (FR-004)
    p_inconsistent, p_diff = validate_p_value_consistency(summary)
    if p_inconsistent:
        is_inconsistent = True
        warnings.append(f"P-value difference exceeds threshold: {p_diff:.4f} > {P_VALUE_THRESHOLD}")
        reasons.append("P_VALUE_MISMATCH")

    # Check effect size consistency (FR-004)
    eff_inconsistent, eff_diff = validate_effect_size_consistency(summary)
    if eff_inconsistent:
        is_inconsistent = True
        warnings.append(f"Effect size relative difference exceeds threshold: {eff_diff:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}")
        reasons.append("EFFECT_SIZE_MISMATCH")

    # Determine data quality warning status
    data_quality_warning = len(warnings) > 0

    record = AuditRecord(
        id=summary.id,
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        reasons=reasons,
        warnings=warnings,
        data_quality_warning=data_quality_warning,
        timestamp=datetime.utcnow().isoformat(),
        # Pass through relevant metrics for downstream filtering
        reported_p_value=summary.reported_p_value,
        reconstructed_p_value=summary.reconstructed_p_value,
        reported_effect_size=summary.reported_effect_size,
        reconstructed_effect_size=summary.reconstructed_effect_size,
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment
    )

    return record

def validate_all(summaries: List[ABTestSummary]) -> List[AuditRecord]:
    """
    Validate a list of summaries and return AuditRecords.
    """
    records = []
    for summary in summaries:
        record = validate_single_summary(summary)
        records.append(record)
        if record.data_quality_warning:
            logger.warning(f"Data quality warning for {record.id}: {record.warnings}")
        if record.is_inconsistent:
            logger.info(f"Inconsistency detected for {record.id}: {record.reasons}")
    return records

def write_audit_report(records: List[AuditRecord], output_path: Path) -> None:
    """
    Write AuditRecords to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [record.model_dump() for record in records]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Audit report written to {output_path}")

def run_validator(
    input_path: Path,
    output_path: Path,
    logger_instance: Optional[AuditLogger] = None
) -> List[AuditRecord]:
    """
    Main entry point for the validator.
    Reads reconstructed summaries from input_path, validates them,
    and writes AuditRecords to output_path.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary.model_validate(s) for s in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries from {input_path}")

    records = validate_all(summaries)
    write_audit_report(records, output_path)

    return records

def main():
    """
    CLI entry point for the validator.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate A/B test summaries for statistical inconsistency.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/reconstructed_summaries.json"),
                        help="Path to reconstructed summaries JSON file.")
    parser.add_argument("--output", type=Path, default=Path("output/audit_report.json"),
                        help="Path to output audit report JSON file.")
    args = parser.parse_args()

    run_validator(args.input, args.output)

if __name__ == "__main__":
    main()
