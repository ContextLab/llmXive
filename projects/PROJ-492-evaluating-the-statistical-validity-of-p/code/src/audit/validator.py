"""
Validator module for A/B test audit pipeline.
Implements inconsistency detection per FR-004 and handles missing data per FR-012.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
import numpy as np

logger = get_default_logger(__name__)

# FR-004 thresholds
P_VALUE_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def validate_single_record(
    summary: ABTestSummary,
    reconstructed: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single A/B test summary against its reconstructed statistical values.
    
    Args:
        summary: The original ABTestSummary object
        reconstructed: Dictionary of reconstructed statistical values
    
    Returns:
        AuditRecord with consistency flags and notes
    """
    notes = []
    flags = []
    data_quality_warning = None
    inconsistency_score = 0.0
    
    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes.append("Missing baseline conversion rate - statistical validation limited")
        data_quality_warning = "Missing baseline conversion rate per FR-012"
        flags.append("missing_baseline")
        # Cannot compute inconsistency without baseline
        return AuditRecord(
            url=summary.url,
            domain=summary.domain,
            p_value_reported=summary.p_value_reported,
            p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
            effect_size_reported=summary.effect_size_reported,
            effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
            sample_size_control=summary.sample_size_control,
            sample_size_treatment=summary.sample_size_treatment,
            is_inconsistent=False,
            inconsistency_reason="missing_baseline",
            notes="; ".join(notes) if notes else None,
            data_quality_warning=data_quality_warning,
            flags=flags,
            inconsistency_score=0.0
        )
    
    # Check for missing other critical fields
    if summary.conversion_rate_treatment is None:
        notes.append("Missing treatment conversion rate")
        data_quality_warning = "Missing treatment conversion rate"
        flags.append("missing_treatment")
    
    if summary.p_value_reported is None:
        notes.append("Missing reported p-value")
        data_quality_warning = "Missing reported p-value"
        flags.append("missing_p_value")
    
    if summary.sample_size_control is None or summary.sample_size_treatment is None:
        notes.append("Missing sample size information")
        data_quality_warning = "Missing sample size"
        flags.append("missing_sample_size")
    
    # Check for sample size mismatch (if both present but different from reconstruction)
    if (reconstructed.get("sample_size_control") is not None and 
        reconstructed.get("sample_size_treatment") is not None):
        if (summary.sample_size_control != reconstructed["sample_size_control"] or
            summary.sample_size_treatment != reconstructed["sample_size_treatment"]):
            notes.append("Sample size mismatch between reported and reconstructed")
            data_quality_warning = "Sample size mismatch"
            flags.append("sample_size_mismatch")
    
    # Calculate inconsistency if we have the necessary data
    if (summary.p_value_reported is not None and 
        reconstructed.get("p_value_reconstructed") is not None and
        summary.effect_size_reported is not None and
        reconstructed.get("effect_size_reconstructed") is not None):
        
        p_diff = abs(summary.p_value_reported - reconstructed["p_value_reconstructed"])
        effect_diff = 0
        if summary.effect_size_reported != 0:
            effect_diff = abs(summary.effect_size_reported - reconstructed["effect_size_reconstructed"]) / abs(summary.effect_size_reported)
        
        is_inconsistent = False
        inconsistency_reason = None
        
        if p_diff > P_VALUE_DIFF_THRESHOLD:
            is_inconsistent = True
            inconsistency_reason = "p_value_diff"
            notes.append(f"P-value difference: {p_diff:.4f} > {P_VALUE_DIFF_THRESHOLD}")
            inconsistency_score += p_diff
        
        if effect_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
            is_inconsistent = True
            if inconsistency_reason:
                inconsistency_reason += "_effect_size"
            else:
                inconsistency_reason = "effect_size"
            notes.append(f"Effect size relative difference: {effect_diff:.4f} > {EFFECT_SIZE_RELATIVE_THRESHOLD}")
            inconsistency_score += effect_diff
        
        if not is_inconsistent:
            notes.append("Statistically consistent within thresholds")
    
    # Build final record
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        is_inconsistent=is_inconsistent if 'is_inconsistent' in locals() else False,
        inconsistency_reason=inconsistency_reason if 'inconsistency_reason' in locals() else None,
        notes="; ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        flags=flags,
        inconsistency_score=inconsistency_score if 'inconsistency_score' in locals() else 0.0
    )

def validate_all_records(
    summaries: List[ABTestSummary],
    reconstructed_list: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate multiple A/B test summaries.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_list: List of reconstructed statistical value dictionaries
    
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(f"Length mismatch: {len(summaries)} summaries vs {len(reconstructed_list)} reconstructed records")
    
    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
        logger.info(f"Validated {summary.url}: inconsistent={record.is_inconsistent}, flags={record.flags}")
    
    return audit_records

def run_validator(
    summaries_path: Path,
    reconstructed_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Run validation on loaded summaries and reconstructed data.
    
    Args:
        summaries_path: Path to JSON file with ABTestSummary objects
        reconstructed_path: Path to JSON file with reconstructed data
        output_path: Path to write audit report
    
    Returns:
        List of AuditRecord objects
    """
    with open(summaries_path, 'r') as f:
        summaries_data = json.load(f)
    
    with open(reconstructed_path, 'r') as f:
        reconstructed_data = json.load(f)
    
    summaries = [ABTestSummary(**s) for s in summaries_data]
    audit_records = validate_all_records(summaries, reconstructed_data)
    
    # Write audit report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([r.model_dump() for r in audit_records], f, indent=2)
    
    logger.info(f"Wrote {len(audit_records)} audit records to {output_path}")
    return audit_records

def main():
    """Entry point for validator script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries against reconstructed statistics")
    parser.add_argument("--summaries", type=Path, required=True, help="Path to summaries JSON")
    parser.add_argument("--reconstructed", type=Path, required=True, help="Path to reconstructed data JSON")
    parser.add_argument("--output", type=Path, required=True, help="Path to output audit report")
    
    args = parser.parse_args()
    
    run_validator(args.summaries, args.reconstructed, args.output)
    print(f"Validation complete. Results written to {args.output}")

if __name__ == "__main__":
    main()