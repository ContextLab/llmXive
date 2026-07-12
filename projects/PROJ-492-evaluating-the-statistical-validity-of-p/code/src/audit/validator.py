"""
Inconsistency validator for A/B test audit pipeline.
Applies FR-004 thresholds and flags data quality issues per FR-012.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

# FR-004 Thresholds
ABSOLUTE_P_DIFF_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

def validate_single_record(
    summary: ABTestSummary,
    reconstructed: Dict[str, Any]
) -> AuditRecord:
    """
    Validate a single A/B test summary against its reconstructed values.
    
    Per FR-012: If baseline conversion rate is missing, flag in audit notes.
    Per FR-004: Flag inconsistencies based on p-value and effect size thresholds.
    Per FR-004b: Flag sample size mismatches with data_quality_warning.
    
    Args:
        summary: The extracted ABTestSummary object
        reconstructed: Dictionary containing reconstructed statistical values
        
    Returns:
        AuditRecord with inconsistency flags and notes
    """
    notes = []
    is_inconsistent = False
    data_quality_warning = None
    inconsistency_reasons = []

    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes.append("baseline conversion rate missing")
        data_quality_warning = "missing_baseline"
        # Still create the record, but note the missing data
        logger.warning(
            f"Missing baseline conversion rate for URL {summary.url}. "
            "Flagged per FR-012."
        )
    
    # Check for missing treatment conversion rate
    if summary.conversion_rate_treatment is None:
        notes.append("treatment conversion rate missing")
        if data_quality_warning is None:
            data_quality_warning = "missing_treatment"
        else:
            data_quality_warning += ",missing_treatment"

    # Reconstruct values may have None if reconstruction failed
    reconstructed_p = reconstructed.get("reconstructed_p_value")
    reported_p = summary.p_value_reported
    
    reconstructed_effect = reconstructed.get("reconstructed_effect_size")
    reported_effect = summary.effect_size_reported

    # Check p-value consistency if both are available
    if reconstructed_p is not None and reported_p is not None:
        try:
            p_diff = abs(reconstructed_p - reported_p)
            if p_diff > ABSOLUTE_P_DIFF_THRESHOLD:
                is_inconsistent = True
                inconsistency_reasons.append(
                    f"p-value diff {p_diff:.4f} > {ABSOLUTE_P_DIFF_THRESHOLD}"
                )
                notes.append(
                    f"p-value inconsistency: |{reported_p:.4f} - {reconstructed_p:.4f}| = {p_diff:.4f}"
                )
        except (TypeError, ValueError) as e:
            logger.warning(f"Error comparing p-values for {summary.url}: {e}")
            notes.append("p-value comparison failed")

    # Check effect size consistency if both are available
    if reconstructed_effect is not None and reported_effect is not None:
        try:
            # Relative difference calculation
            if reported_effect != 0:
                rel_diff = abs(reconstructed_effect - reported_effect) / abs(reported_effect)
            else:
                rel_diff = float('inf') if reconstructed_effect != 0 else 0
            
            if rel_diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
                is_inconsistent = True
                inconsistency_reasons.append(
                    f"effect-size rel-diff {rel_diff:.4f} > {RELATIVE_EFFECT_SIZE_THRESHOLD}"
                )
                notes.append(
                    f"effect-size inconsistency: rel-diff={rel_diff:.4f}"
                )
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Error comparing effect sizes for {summary.url}: {e}")
            notes.append("effect-size comparison failed")

    # Check for sample size mismatches (FR-004b)
    if (summary.sample_size_control is not None and 
        summary.sample_size_treatment is not None and
        reconstructed.get("control_n") is not None and
        reconstructed.get("treatment_n") is not None):
        
        control_diff = abs(summary.sample_size_control - reconstructed.get("control_n", 0))
        treatment_diff = abs(summary.sample_size_treatment - reconstructed.get("treatment_n", 0))
        
        if control_diff > 0 or treatment_diff > 0:
            if data_quality_warning:
                data_quality_warning += ",sample_size_mismatch"
            else:
                data_quality_warning = "sample_size_mismatch"
            notes.append(
                f"sample-size mismatch: control_diff={control_diff}, treatment_diff={treatment_diff}"
            )
            # Per FR-004b, sample-size mismatch entries are excluded from aggregate prevalence
            # but we still flag them here

    # Build notes string
    notes_str = "; ".join(notes) if notes else "consistent"

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        test_type=summary.test_type,
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect,
        reconstructed_effect_size=reconstructed_effect,
        is_inconsistent=is_inconsistent,
        inconsistency_reasons=inconsistency_reasons,
        notes=notes_str,
        data_quality_warning=data_quality_warning
    )

def validate_all_records(
    summaries: List[ABTestSummary],
    reconstructed_list: List[Dict[str, Any]]
) -> List[AuditRecord]:
    """
    Validate all summaries against their reconstructed values.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_list: List of reconstructed value dictionaries
        
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(
            f"Number of summaries ({len(summaries)}) does not match "
            f"number of reconstructed records ({len(reconstructed_list)})"
        )

    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
        if record.data_quality_warning:
            logger.info(
                f"Data quality warning for {summary.url}: {record.data_quality_warning}"
            )
    
    return audit_records

def write_audit_report(
    audit_records: List[AuditRecord],
    output_path: Path
) -> None:
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
            "test_type": record.test_type,
            "reported_p_value": record.reported_p_value,
            "reconstructed_p_value": record.reconstructed_p_value,
            "reported_effect_size": record.reported_effect_size,
            "reconstructed_effect_size": record.reconstructed_effect_size,
            "is_inconsistent": record.is_inconsistent,
            "inconsistency_reasons": record.inconsistency_reasons,
            "notes": record.notes,
            "data_quality_warning": record.data_quality_warning
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2, default=str)
    
    logger.info(f"Audit report written to {output_path}")

def run_validator(
    summaries_path: Path,
    reconstructed_path: Path,
    output_path: Path
) -> List[AuditRecord]:
    """
    Run the full validation pipeline.
    
    Args:
        summaries_path: Path to extracted summaries JSON
        reconstructed_path: Path to reconstructed values JSON
        output_path: Path for output audit report
        
    Returns:
        List of AuditRecord objects
    """
    # Load summaries
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**item) for item in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries from {summaries_path}")

    # Load reconstructed values
    with open(reconstructed_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)
    
    logger.info(f"Loaded {len(reconstructed_data)} reconstructed records from {reconstructed_path}")

    # Validate
    audit_records = validate_all_records(summaries, reconstructed_data)
    
    # Write report
    write_audit_report(audit_records, output_path)
    
    # Log summary statistics
    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    warning_count = sum(1 for r in audit_records if r.data_quality_warning)
    
    logger.info(f"Validation complete: {inconsistent_count} inconsistent, "
               f"{warning_count} with data quality warnings")
    
    return audit_records

def main():
    """CLI entry point for validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test audit records")
    parser.add_argument(
        "--summaries", 
        type=Path, 
        default=Path("data/processed/extracted_summaries.json"),
        help="Path to extracted summaries JSON"
    )
    parser.add_argument(
        "--reconstructed",
        type=Path,
        default=Path("data/processed/reconstructed_values.json"),
        help="Path to reconstructed values JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path for output audit report"
    )
    
    args = parser.parse_args()
    
    if not args.summaries.exists():
        logger.error(f"Summaries file not found: {args.summaries}")
        return 1
    
    if not args.reconstructed.exists():
        logger.error(f"Reconstructed file not found: {args.reconstructed}")
        return 1
    
    try:
        run_validator(args.summaries, args.reconstructed, args.output)
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())