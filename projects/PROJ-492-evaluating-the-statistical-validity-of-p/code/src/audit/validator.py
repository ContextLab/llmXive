"""
Inconsistency validator for A/B test audit pipeline.
Applies FR-004 thresholds and flags data quality issues per FR-012.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.reconstructor import reconstruct_single_summary
from code.src.config import SEED

logger = get_default_logger(__name__)

# FR-004 Thresholds
P_VALUE_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single ABTestSummary against its reconstructed statistical values.
    
    Implements FR-004 (inconsistency thresholds) and FR-012 (missing baseline flagging).
    
    Args:
        summary: The original extracted A/B test summary
        reconstructed: Dictionary of reconstructed statistical values
        
    Returns:
        AuditRecord with consistency flags and notes
    """
    notes = []
    inconsistencies = []
    data_quality_warning = None
    is_consistent = True

    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes.append("baseline conversion rate missing")
        data_quality_warning = "Missing baseline conversion rate prevents full statistical validation"
        # Note: We still create the record, but flag the data quality issue
        # Don't mark as inconsistent due to missing data, just flag it
    else:
        # Only perform consistency checks if we have the necessary data
        p_reported = summary.p_value_reported
        p_reconstructed = reconstructed.get('p_value')
        effect_reported = summary.effect_size_reported
        effect_reconstructed = reconstructed.get('effect_size')
        
        # Check p-value consistency (FR-004)
        if p_reported is not None and p_reconstructed is not None:
            if abs(p_reported - p_reconstructed) > P_VALUE_THRESHOLD:
                inconsistencies.append({
                    "type": "p_value_mismatch",
                    "reported": p_reported,
                    "reconstructed": p_reconstructed,
                    "difference": abs(p_reported - p_reconstructed)
                })
                notes.append(f"p-value discrepancy: reported={p_reported:.4f}, reconstructed={p_reconstructed:.4f}")
                is_consistent = False

        # Check effect size consistency (FR-004)
        if effect_reported is not None and effect_reconstructed is not None:
            if effect_reported != 0:
                relative_diff = abs(effect_reported - effect_reconstructed) / abs(effect_reported)
                if relative_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
                    inconsistencies.append({
                        "type": "effect_size_mismatch",
                        "reported": effect_reported,
                        "reconstructed": effect_reconstructed,
                        "relative_difference": relative_diff
                    })
                    notes.append(f"Effect size discrepancy: reported={effect_reported:.4f}, reconstructed={effect_reconstructed:.4f} ({relative_diff:.1%} diff)")
                    is_consistent = False

    # Check for sample size mismatches (if applicable)
    if summary.sample_size_control is not None and summary.sample_size_treatment is not None:
        if summary.sample_size_control <= 0 or summary.sample_size_treatment <= 0:
            notes.append("Invalid sample sizes detected")
            data_quality_warning = "Sample sizes must be positive integers"

    # Create the audit record
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_consistent=is_consistent,
        inconsistencies=inconsistencies,
        notes="; ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        publication_year=summary.publication_year,
        test_type=summary.test_type
    )
    
    return audit_record

def validate_all_records(summaries: List[ABTestSummary], reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validate multiple ABTestSummary records.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_list: List of reconstructed statistical value dictionaries
        
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(f"Number of summaries ({len(summaries)}) must match number of reconstructed records ({len(reconstructed_list)})")
    
    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
        logger.info(f"Validated {summary.url}: consistent={record.is_consistent}")
    
    return audit_records

def write_audit_records_to_json(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write audit records to a JSON file.
    
    Args:
        audit_records: List of AuditRecord objects
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records_data = []
    for record in audit_records:
        record_dict = asdict(record)
        # Convert None to null explicitly for JSON serialization
        for key, value in record_dict.items():
            if value is None:
                record_dict[key] = None
        records_data.append(record_dict)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records_data, f, indent=2)
    
    logger.info(f"Wrote {len(audit_records)} audit records to {output_path}")

def main():
    """
    Main entry point for validation script.
    Reads reconstructed data, validates against summaries, writes audit report.
    """
    # Default paths
    summaries_path = Path("data/processed/extracted_summaries.json")
    reconstructed_path = Path("data/processed/reconstructed_stats.json")
    output_path = Path("output/audit_report.json")
    
    # Parse command line arguments if needed
    import sys
    if len(sys.argv) > 1:
        summaries_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        reconstructed_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    
    # Load data
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    with open(reconstructed_path, 'r', encoding='utf-8') as f:
        reconstructed_data = json.load(f)
    
    # Convert to objects
    summaries = [ABTestSummary(**item) for item in summaries_data]
    reconstructed_list = reconstructed_data if isinstance(reconstructed_data, list) else [reconstructed_data]
    
    # Validate
    audit_records = validate_all_records(summaries, reconstructed_list)
    
    # Write results
    write_audit_records_to_json(audit_records, output_path)
    
    # Summary statistics
    consistent_count = sum(1 for r in audit_records if r.is_consistent)
    inconsistent_count = len(audit_records) - consistent_count
    warning_count = sum(1 for r in audit_records if r.data_quality_warning is not None)
    
    logger.info(f"Validation complete: {consistent_count} consistent, {inconsistent_count} inconsistent, {warning_count} with warnings")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())