"""
Validator module for T025: Implement inconsistency validator.
Applies FR-004 thresholds and FR-012 missing baseline checks.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED

logger = get_default_logger(__name__)

# FR-004 Thresholds
ABSOLUTE_P_DIFF_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single ABTestSummary against its reconstructed statistics.
    
    Per FR-012: If baseline conversion rate is missing, flag in audit notes.
    Per FR-004: Check p-value and effect size consistency.
    """
    notes = []
    data_quality_warning = None
    is_inconsistent = False
    
    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        warning_msg = "baseline conversion rate missing"
        notes.append(f"WARNING: {warning_msg}")
        data_quality_warning = warning_msg
        # Even if data is missing, we don't mark as statistically inconsistent
        # because we cannot verify, but we must flag it.
        # However, per strict audit logic, if we can't compute, we might mark as inconclusive.
        # For this task, we flag it as a data quality warning.
    else:
        # Proceed with statistical consistency checks only if baseline exists
        
        # Extract reconstructed values
        p_reconstructed = reconstructed.get("p_value_reconstructed")
        p_reported = summary.p_value_reported
        
        effect_size_reconstructed = reconstructed.get("effect_size_reconstructed")
        effect_size_reported = summary.effect_size_reported
        
        # FR-004: Absolute p-value difference check
        if p_reconstructed is not None and p_reported is not None:
            p_diff = abs(p_reconstructed - p_reported)
            if p_diff > ABSOLUTE_P_DIFF_THRESHOLD:
                notes.append(f"P-value inconsistency: |{p_reconstructed:.4f} - {p_reported:.4f}| = {p_diff:.4f} > {ABSOLUTE_P_DIFF_THRESHOLD}")
                is_inconsistent = True
        
        # FR-004: Relative effect size difference check
        if effect_size_reconstructed is not None and effect_size_reported is not None:
            if effect_size_reported != 0:
                rel_diff = abs(effect_size_reconstructed - effect_size_reported) / abs(effect_size_reported)
                if rel_diff > RELATIVE_EFFECT_SIZE_THRESHOLD:
                    notes.append(f"Effect size inconsistency: relative diff {rel_diff:.2%} > {RELATIVE_EFFECT_SIZE_THRESHOLD:.0%}")
                    is_inconsistent = True
            else:
                # Avoid division by zero if reported effect is 0
                if abs(effect_size_reconstructed) > 0.001: # Arbitrary small threshold
                     notes.append("Effect size inconsistency: reported 0 but reconstructed non-zero")
                     is_inconsistent = True

    # Construct the AuditRecord
    audit_record = AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        notes="; ".join(notes) if notes else None,
        data_quality_warning=data_quality_warning,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=reconstructed.get("p_value_reconstructed"),
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=reconstructed.get("effect_size_reconstructed"),
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment,
        test_type=summary.test_type,
        publication_year=summary.publication_year
    )
    
    return audit_record

def validate_all_records(summaries: List[ABTestSummary], reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validate a list of summaries against their reconstructed statistics.
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError("Number of summaries and reconstructed records must match")
    
    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
    
    return audit_records

def write_audit_report(audit_records: List[AuditRecord], output_path: Path) -> None:
    """
    Write the audit records to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(record) for record in audit_records]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Audit report written to {output_path}")

def main():
    """
    Entry point for the validator script.
    Expects input JSON of summaries and reconstructed data (or runs reconstruction internally if needed).
    For this task, we assume reconstruction is done separately or passed in.
    This main function is primarily for CLI invocation to validate a batch.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON with summaries and reconstructions")
    parser.add_argument("--output", type=str, required=True, help="Path to output audit report JSON")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summaries = []
    reconstructed_list = []
    
    for item in data:
        # Assuming input format: {"summary": {...}, "reconstructed": {...}}
        summary_dict = item.get("summary", {})
        reconstructed_dict = item.get("reconstructed", {})
        
        summary = ABTestSummary(**summary_dict)
        summaries.append(summary)
        reconstructed_list.append(reconstructed_dict)
    
    audit_records = validate_all_records(summaries, reconstructed_list)
    write_audit_report(audit_records, output_path)
    
    return 0

if __name__ == "__main__":
    exit(main())
