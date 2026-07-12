"""
Validator module for T025: Implement inconsistency validator applying FR-004 thresholds
and handling missing baseline data per FR-012.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.audit.reconstructor import reconstruct_single_summary

logger = get_default_logger()

# FR-004 Thresholds
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single A/B test summary against reconstructed statistics.
    Flags missing baseline conversion rates per FR-012.
    """
    notes = []
    data_quality_warning = None
    is_inconsistent = False

    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes.append("baseline conversion rate missing")
        data_quality_warning = "Missing baseline conversion rate prevents full statistical validation"
        # Even with missing baseline, we can note the issue but cannot compute inconsistency
        # We still create the record with the warning
        return AuditRecord(
            url=summary.url,
            domain=summary.domain,
            is_inconsistent=False,  # Cannot determine inconsistency without baseline
            p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
            p_value_reported=summary.p_value_reported,
            effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
            effect_size_reported=summary.effect_size_reported,
            notes="; ".join(notes) if notes else None,
            data_quality_warning=data_quality_warning,
            validation_method="missing_baseline_check"
        )

    # Check for missing treatment rate
    if summary.conversion_rate_treatment is None:
        notes.append("treatment conversion rate missing")
        data_quality_warning = "Missing treatment conversion rate prevents full statistical validation"
        return AuditRecord(
            url=summary.url,
            domain=summary.domain,
            is_inconsistent=False,
            p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
            p_value_reported=summary.p_value_reported,
            effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
            effect_size_reported=summary.effect_size_reported,
            notes="; ".join(notes) if notes else None,
            data_quality_warning=data_quality_warning,
            validation_method="missing_treatment_check"
        )

    # Calculate absolute p-value difference
    p_diff = 0.0
    if summary.p_value_reported is not None and reconstructed.get("p_value_reconstructed") is not None:
        p_diff = abs(summary.p_value_reported - reconstructed["p_value_reconstructed"])

    # Calculate relative effect size difference
    effect_diff_rel = 0.0
    if summary.effect_size_reported is not None and reconstructed.get("effect_size_reconstructed") is not None:
        reported = summary.effect_size_reported
        reconstructed_eff = reconstructed["effect_size_reconstructed"]
        if reported != 0:
            effect_diff_rel = abs(reported - reconstructed_eff) / abs(reported)
        else:
            effect_diff_rel = abs(reported - reconstructed_eff)

    # Apply FR-004 thresholds
    if p_diff > P_VALUE_THRESHOLD:
        notes.append(f"p-value difference ({p_diff:.4f}) exceeds threshold ({P_VALUE_THRESHOLD})")
        is_inconsistent = True

    if effect_diff_rel > EFFECT_SIZE_RELATIVE_THRESHOLD:
        notes.append(f"effect size relative difference ({effect_diff_rel:.2%}) exceeds threshold ({EFFECT_SIZE_RELATIVE_THRESHOLD:.0%})")
        is_inconsistent = True

    # Check for sample size mismatch (FR-004b)
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        if summary.sample_size_control != summary.sample_size_treatment:
            # This is a warning, not necessarily an inconsistency in the test itself
            # but per FR-004b we flag it
            notes.append("sample size mismatch between control and treatment")
            if data_quality_warning is None:
                data_quality_warning = "Sample size mismatch detected"
            else:
                data_quality_warning += "; Sample size mismatch detected"

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
        p_value_reported=summary.p_value_reported,
        effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
        effect_size_reported=summary.effect_size_reported,
        notes="; ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        validation_method="threshold_check"
    )

def validate_all_records(summaries: List[ABTestSummary], reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validate a batch of summaries against their reconstructed statistics.
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError("Number of summaries must match number of reconstructed records")

    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)

    return audit_records

def main():
    """
    Main entry point for running validation on a dataset.
    Expects input files to be configured or passed via arguments.
    """
    logger.info("Starting validation process")
    # This would typically load from files, but for now we just log
    logger.info("Validation module loaded successfully")

if __name__ == "__main__":
    main()