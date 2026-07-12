"""
Inconsistency Validator for A/B Test Summaries.

Applies FR-004 thresholds to detect statistical inconsistencies between
reported and reconstructed values, and handles sample-size mismatches
per FR-004b by flagging them and excluding them from aggregate prevalence.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED

# Set seed for any stochastic operations (though this module is deterministic)
np.random.seed(SEED)

# Thresholds per FR-004
THRESHOLD_ABSOLUTE_P_DIFF = 0.05
THRESHOLD_RELATIVE_EFFECT_SIZE = 0.05  # 5%

logger: AuditLogger = get_default_logger()


def calculate_effect_size_diff(
    reported_effect: Optional[float],
    reconstructed_effect: Optional[float]
) -> Optional[float]:
    """
    Calculate the relative difference in effect sizes.
    Formula: |reported - reconstructed| / |reconstructed|
    Returns None if reconstructed is zero or missing.
    """
    if reported_effect is None or reconstructed_effect is None:
        return None
    
    if abs(reconstructed_effect) < 1e-9:
        # Avoid division by zero
        if abs(reported_effect) > 1e-9:
            return float('inf')
        return 0.0
        
    return abs(reported_effect - reconstructed_effect) / abs(reconstructed_effect)


def validate_single_summary(
    summary: ABTestSummary,
    reconstructed: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single ABTestSummary against its reconstructed values.
    
    Checks:
    1. Absolute p-value difference > 0.05 (FR-004)
    2. Relative effect size difference > 5% (FR-004)
    3. Sample size mismatch (FR-004b) -> flags data_quality_warning
    
    Returns an AuditRecord with appropriate flags and messages.
    """
    record_id = summary.url_hash or "unknown"
    warnings = []
    inconsistencies = []
    is_inconsistent = False
    data_quality_warning = False
    exclusion_reason = None

    # Extract reported and reconstructed values
    reported_p = summary.p_value
    reconstructed_p = reconstructed.get('reconstructed_p_value')
    
    reported_effect = summary.effect_size
    reconstructed_effect = reconstructed.get('reconstructed_effect_size')
    
    reported_n = summary.sample_size
    reconstructed_n = reconstructed.get('reconstructed_sample_size')

    # 1. Check P-value consistency (FR-004)
    if reported_p is not None and reconstructed_p is not None:
        p_diff = abs(reported_p - reconstructed_p)
        if p_diff > THRESHOLD_ABSOLUTE_P_DIFF:
            inconsistencies.append(
                f"P-value difference {p_diff:.4f} exceeds threshold {THRESHOLD_ABSOLUTE_P_DIFF}"
            )
            is_inconsistent = True

    # 2. Check Effect Size consistency (FR-004)
    if reported_effect is not None and reconstructed_effect is not None:
        rel_diff = calculate_effect_size_diff(reported_effect, reconstructed_effect)
        if rel_diff is not None and rel_diff > THRESHOLD_RELATIVE_EFFECT_SIZE:
            inconsistencies.append(
                f"Effect size relative difference {rel_diff:.2%} exceeds threshold {THRESHOLD_RELATIVE_EFFECT_SIZE:.0%}"
            )
            is_inconsistent = True

    # 3. Check Sample Size Mismatch (FR-004b)
    if reported_n is not None and reconstructed_n is not None:
        if reported_n != reconstructed_n:
            data_quality_warning = True
            exclusion_reason = "sample_size_mismatch"
            warnings.append(
                f"Sample size mismatch: reported={reported_n}, reconstructed={reconstructed_n}. "
                "Record excluded from aggregate prevalence estimates per FR-004b."
            )
            # Note: We do NOT mark as statistical inconsistency solely based on sample size,
            # but we flag it for exclusion.
    
    # Construct the AuditRecord
    audit_record = AuditRecord(
        id=record_id,
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        inconsistency_reason=inconsistencies if inconsistencies else None,
        data_quality_warning=data_quality_warning,
        warning_message=warnings if warnings else None,
        exclusion_reason=exclusion_reason,
        metadata={
            "reported_p_value": reported_p,
            "reconstructed_p_value": reconstructed_p,
            "reported_effect_size": reported_effect,
            "reconstructed_effect_size": reconstructed_effect,
            "reported_sample_size": reported_n,
            "reconstructed_sample_size": reconstructed_n,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    )

    return audit_record


def validate_all_summaries(
    summaries: List[ABTestSummary],
    reconstructed_results: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate a list of summaries against their corresponding reconstructed results.
    
    Args:
        summaries: List of ABTestSummary objects extracted from HTML.
        reconstructed_results: List of dicts containing reconstruction outputs
                             (p-value, effect size, sample size).
    
    Returns:
        List of AuditRecord objects.
    """
    if len(summaries) != len(reconstructed_results):
        logger.error(
            "ERR-099",
            f"Length mismatch between summaries ({len(summaries)}) and "
            f"reconstructed results ({len(reconstructed_results)})"
        )
        # Proceed anyway, handling index errors gracefully
    
    records = []
    for i, summary in enumerate(summaries):
        recon = reconstructed_results[i] if i < len(reconstructed_results) else {}
        record = validate_single_summary(summary, recon)
        records.append(record)
        if record.data_quality_warning:
            logger.warning(
                "ERR-045",
                f"Sample size mismatch detected for {summary.url_hash}"
            )
        if record.is_inconsistent:
            logger.warning(
                "ERR-044",
                f"Statistical inconsistency detected for {summary.url_hash}"
            )
    
    return records


def write_audit_report(
    records: List[AuditRecord],
    output_path: str
) -> None:
    """
    Write the list of AuditRecord objects to a JSON file.
    
    Args:
        records: List of AuditRecord objects.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert dataclasses to dicts
    records_dict = [
        {
            "id": r.id,
            "url": r.url,
            "domain": r.domain,
            "is_inconsistent": r.is_inconsistent,
            "inconsistency_reason": r.inconsistency_reason,
            "data_quality_warning": r.data_quality_warning,
            "warning_message": r.warning_message,
            "exclusion_reason": r.exclusion_reason,
            "metadata": r.metadata
        }
        for r in records
    ]
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records_dict, f, indent=2, default=str)
    
    logger.info("INF-001", f"Audit report written to {output_path}")


def main() -> int:
    """
    Main entry point for the validator.
    
    Reads reconstructed results from data/reconstruction_results.json
    and summaries from data/extracted_summaries.json (or similar paths
    established by T023 and T020).
    
    Writes output to output/audit_report.json.
    """
    # Define paths relative to project root
    # Assuming standard paths established by previous tasks
    summaries_path = Path("data/extracted_summaries.json")
    recon_path = Path("data/reconstruction_results.json")
    output_path = Path("output/audit_report.json")
    
    if not summaries_path.exists():
        logger.error("ERR-002", f"Summaries file not found: {summaries_path}")
        return 1
    
    if not recon_path.exists():
        logger.error("ERR-002", f"Reconstruction results file not found: {recon_path}")
        return 1
    
    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    # Convert to ABTestSummary objects
    # Assuming the JSON structure matches the data model fields
    summaries = [ABTestSummary(**item) for item in summaries_data]
    
    # Load reconstruction results
    with open(recon_path, 'r', encoding='utf-8') as f:
        recon_data = json.load(f)
    
    # Validate
    records = validate_all_summaries(summaries, recon_data)
    
    # Write report
    write_audit_report(records, str(output_path))
    
    # Summary stats
    inconsistent_count = sum(1 for r in records if r.is_inconsistent)
    warning_count = sum(1 for r in records if r.data_quality_warning)
    
    logger.info("INF-002", f"Validation complete. Total: {len(records)}, "
                f"Inconsistent: {inconsistent_count}, Warnings: {warning_count}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
