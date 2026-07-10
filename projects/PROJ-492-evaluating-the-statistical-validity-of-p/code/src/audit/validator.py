"""
Validator module for T025: Inconsistency validation and T025b: Missing baseline flagging.

Implements FR-004 thresholds (absolute p-difference > 0.05, relative effect-size > 5%)
and FR-012 (flag missing baseline conversion rates).
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED
import numpy as np

# Ensure deterministic behavior
np.random.seed(SEED)

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single AB test summary against its reconstructed values.
    
    Checks:
    1. Absolute p-value difference > 0.05 (FR-004)
    2. Relative effect-size difference > 5% (FR-004)
    3. Missing baseline conversion rate flag (FR-012)
    4. Sample size mismatch (FR-004b)
    
    Returns an AuditRecord with appropriate flags and notes.
    """
    logger = get_default_logger()
    notes = []
    data_quality_warning = None
    is_inconsistent = False
    
    # Check for missing baseline conversion rate (FR-012)
    if summary.conversion_rate_control is None:
        notes.append("baseline conversion rate missing")
        data_quality_warning = "Missing baseline conversion rate - statistical validity cannot be fully assessed"
        # Still create the record but flag the quality issue
    
    # Check for missing treatment conversion rate
    if summary.conversion_rate_treatment is None:
        notes.append("treatment conversion rate missing")
        if data_quality_warning:
            data_quality_warning += "; "
        data_quality_warning += "Missing treatment conversion rate"
    
    # Calculate reconstructed p-value if available
    reconstructed_p = reconstructed.get("reconstructed_p_value")
    reported_p = summary.p_value_reported
    
    if reconstructed_p is not None and reported_p is not None:
        p_diff = abs(reconstructed_p - reported_p)
        if p_diff > 0.05:
            notes.append(f"p-value discrepancy: |{reported_p:.4f} - {reconstructed_p:.4f}| = {p_diff:.4f} > 0.05")
            is_inconsistent = True
    
    # Calculate reconstructed effect size if available
    reconstructed_effect = reconstructed.get("reconstructed_effect_size")
    reported_effect = summary.effect_size_reported
    
    if reconstructed_effect is not None and reported_effect is not None:
        # Relative difference
        if reported_effect != 0:
            rel_diff = abs(reconstructed_effect - reported_effect) / abs(reported_effect)
            if rel_diff > 0.05:  # 5% threshold
                notes.append(f"effect size discrepancy: rel_diff = {rel_diff:.4f} > 0.05")
                is_inconsistent = True
        else:
            # Absolute difference if reported effect is 0
            if abs(reconstructed_effect - reported_effect) > 0.05:
                notes.append(f"effect size discrepancy: abs_diff = {abs(reconstructed_effect - reported_effect):.4f} > 0.05")
                is_inconsistent = True
    
    # Check sample size mismatch (FR-004b)
    sample_size_mismatch = reconstructed.get("sample_size_mismatch", False)
    if sample_size_mismatch:
        notes.append("sample size mismatch detected - excluded from aggregate prevalence")
        if data_quality_warning:
            data_quality_warning += "; "
        data_quality_warning = "Sample size mismatch - summary excluded from aggregate prevalence estimates"
    
    # Construct notes string
    notes_str = "; ".join(notes) if notes else "All checks passed"
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect,
        reconstructed_effect_size=reconstructed_effect,
        is_inconsistent=is_inconsistent,
        notes=notes_str,
        data_quality_warning=data_quality_warning,
        sample_size_mismatch=sample_size_mismatch
    )

def validate_all_records(summaries: List[ABTestSummary], 
                        reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validate all summaries against their reconstructed values.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_list: List of dictionaries with reconstructed values
        
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(f"Length mismatch: {len(summaries)} summaries vs {len(reconstructed_list)} reconstructed records")
    
    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
    
    return audit_records

def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write audit records to JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records_data = []
    for record in audit_records:
        records_data.append({
            "url": record.url,
            "domain": record.domain,
            "publication_year": record.publication_year,
            "reported_p_value": record.reported_p_value,
            "reconstructed_p_value": record.reconstructed_p_value,
            "reported_effect_size": record.reported_effect_size,
            "reconstructed_effect_size": record.reconstructed_effect_size,
            "is_inconsistent": record.is_inconsistent,
            "notes": record.notes,
            "data_quality_warning": record.data_quality_warning,
            "sample_size_mismatch": record.sample_size_mismatch
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2, default=str)
    
    logger = get_default_logger()
    logger.info(f"Audit report written to {output_path}")

def main() -> None:
    """
    Main entry point for validator.
    
    Reads reconstructed summaries from data/reconstructed_summaries.json
    and writes audit report to output/audit_report.json
    """
    logger = get_default_logger()
    logger.info("Starting validation process")
    
    # Load reconstructed summaries
    reconstructed_path = Path("data/reconstructed_summaries.json")
    if not reconstructed_path.exists():
        logger.error(f"Reconstructed summaries not found at {reconstructed_path}")
        return
    
    with open(reconstructed_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)
    
    # Load original summaries
    summaries_path = Path("data/extracted_summaries.json")
    if not summaries_path.exists():
        logger.error(f"Extracted summaries not found at {summaries_path}")
        return
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    # Convert to ABTestSummary objects
    summaries = []
    for item in summaries_data:
        summary = ABTestSummary(
            url=item["url"],
            domain=item["domain"],
            sample_size_control=item.get("sample_size_control"),
            sample_size_treatment=item.get("sample_size_treatment"),
            conversion_rate_control=item.get("conversion_rate_control"),
            conversion_rate_treatment=item.get("conversion_rate_treatment"),
            p_value_reported=item.get("p_value_reported"),
            effect_size_reported=item.get("effect_size_reported"),
            test_type=item.get("test_type", "binary"),
            publication_year=item.get("publication_year")
        )
        summaries.append(summary)
    
    # Validate all records
    audit_records = validate_all_records(summaries, reconstructed_data)
    
    # Write audit report
    output_path = Path("output/audit_report.json")
    write_audit_report(audit_records, output_path)
    
    # Log summary statistics
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    missing_baseline_count = sum(1 for r in audit_records if r.data_quality_warning and "missing baseline" in r.data_quality_warning.lower())
    
    logger.info(f"Validation complete: {len(audit_records)} records processed")
    logger.info(f"Inconsistent records: {inconsistent_count}")
    logger.info(f"Records with missing baseline: {missing_baseline_count}")

if __name__ == "__main__":
    main()