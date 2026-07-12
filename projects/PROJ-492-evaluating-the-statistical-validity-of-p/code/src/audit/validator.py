"""
Validator module for T025: Inconsistency validation and T025b: Missing baseline flagging.
Applies FR-004 thresholds and flags missing baselines per FR-012.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, get_error_message, AuditLogger

logger = get_default_logger(__name__)

# FR-004 Thresholds
P_VALUE_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def validate_single_record(summary: ABTestSummary, reconstructed: Dict[str, Any]) -> AuditRecord:
    """
    Validate a single A/B test summary against its reconstructed statistical values.
    
    Per FR-012: If baseline conversion rate is missing, flag in audit notes.
    Per FR-004: Check p-value difference and effect size consistency.
    """
    notes = []
    data_quality_warning = None
    is_inconsistent = False
    
    # Check for missing baseline conversion rate (FR-012)
    if summary.conversion_rate_control is None:
        missing_msg = "missing baseline conversion rate"
        notes.append(missing_msg)
        data_quality_warning = f"Data quality issue: {missing_msg}. Per FR-012, this prevents accurate statistical validation."
        # Even if baseline is missing, we can still flag inconsistency if other fields conflict
        # but we note the limitation
        logger.warning(f"Missing baseline for {summary.url}: {missing_msg}")
    
    # Check for missing treatment conversion rate
    if summary.conversion_rate_treatment is None:
        missing_treatment_msg = "missing treatment conversion rate"
        notes.append(missing_treatment_msg)
        if not data_quality_warning:
            data_quality_warning = f"Data quality issue: {missing_treatment_msg}."
    
    # If we have the necessary data, perform statistical consistency checks
    if (summary.conversion_rate_control is not None and 
        summary.conversion_rate_treatment is not None and
        summary.p_value_reported is not None and
        reconstructed.get('p_value_reconstructed') is not None):
        
        reported_p = summary.p_value_reported
        reconstructed_p = reconstructed['p_value_reconstructed']
        
        # Absolute p-value difference check (FR-004)
        p_diff = abs(reported_p - reconstructed_p)
        if p_diff > P_VALUE_DIFF_THRESHOLD:
            notes.append(f"P-value discrepancy: reported={reported_p:.4f}, reconstructed={reconstructed_p:.4f}, diff={p_diff:.4f} > {P_VALUE_DIFF_THRESHOLD}")
            is_inconsistent = True
        
        # Relative effect size check (FR-004)
        if summary.effect_size_reported is not None and reconstructed.get('effect_size_reconstructed') is not None:
            reported_effect = summary.effect_size_reported
            reconstructed_effect = reconstructed['effect_size_reconstructed']
            
            if abs(reported_effect) > 0:  # Avoid division by zero
                relative_diff = abs(reported_effect - reconstructed_effect) / abs(reported_effect)
                if relative_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
                    notes.append(f"Effect size discrepancy: reported={reported_effect:.4f}, reconstructed={reconstructed_effect:.4f}, relative_diff={relative_diff:.2%} > {EFFECT_SIZE_RELATIVE_THRESHOLD:.0%}")
                    is_inconsistent = True
            else:
                # If reported effect is 0 but reconstructed is not, that's a discrepancy
                if reconstructed_effect != 0:
                    notes.append(f"Effect size discrepancy: reported=0, reconstructed={reconstructed_effect:.4f}")
                    is_inconsistent = True
    elif summary.conversion_rate_control is not None and summary.conversion_rate_treatment is not None:
        # We have conversion rates but missing p-value or reconstruction failed
        notes.append("Missing p-value reported or reconstruction failed for consistency check")
    
    # Check for sample size mismatch (FR-004b)
    if (summary.sample_size_control is not None and 
        summary.sample_size_treatment is not None and
        summary.sample_size_control != summary.sample_size_treatment):
        notes.append(f"Sample size mismatch: control={summary.sample_size_control}, treatment={summary.sample_size_treatment}")
        # Per FR-004b, this should be excluded from aggregate prevalence but flagged here
        if not data_quality_warning:
            data_quality_warning = "Sample size mismatch detected."
        else:
            data_quality_warning += " Sample size mismatch detected."
    
    # Construct notes string
    notes_str = "; ".join(notes) if notes else "No issues detected."
    
    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        publication_year=summary.publication_year,
        is_inconsistent=is_inconsistent,
        notes=notes_str,
        data_quality_warning=data_quality_warning,
        p_value_reported=summary.p_value_reported,
        p_value_reconstructed=reconstructed.get('p_value_reconstructed'),
        effect_size_reported=summary.effect_size_reported,
        effect_size_reconstructed=reconstructed.get('effect_size_reconstructed'),
        sample_size_control=summary.sample_size_control,
        sample_size_treatment=summary.sample_size_treatment
    )

def validate_all_records(summaries: List[ABTestSummary], 
                         reconstructed_list: List[Dict[str, Any]]) -> List[AuditRecord]:
    """
    Validate all records in a batch.
    
    Args:
        summaries: List of ABTestSummary objects
        reconstructed_list: List of dictionaries with reconstructed statistical values
        
    Returns:
        List of AuditRecord objects
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(f"Mismatch in number of summaries ({len(summaries)}) and reconstructed records ({len(reconstructed_list)})")
    
    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
        if record.data_quality_warning:
            logger.warning(f"Data quality warning for {summary.url}: {record.data_quality_warning}")
    
    return audit_records

def run_validator(input_json_path: str, output_json_path: str) -> Tuple[int, int]:
    """
    Run the validator on a JSON file of ABTestSummary objects.
    
    Args:
        input_json_path: Path to JSON file containing ABTestSummary objects
        output_json_path: Path to write AuditRecord objects
        
    Returns:
        Tuple of (total_records, inconsistent_count)
    """
    logger.info(f"Starting validation of {input_json_path}")
    
    # Load summaries
    with open(input_json_path, 'r') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**data) for data in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")
    
    # Reconstruct statistics (assuming reconstructor is called here or passed in)
    # For this validator, we assume reconstruction is done externally or we do it here
    from code.src.audit.reconstructor import reconstruct_all
    reconstructed_list = reconstruct_all(summaries)
    
    # Validate
    audit_records = validate_all_records(summaries, reconstructed_list)
    
    # Write output
    audit_records_data = [record.model_dump() for record in audit_records]
    with open(output_json_path, 'w') as f:
        json.dump(audit_records_data, f, indent=2)
    
    inconsistent_count = sum(1 for record in audit_records if record.is_inconsistent)
    logger.info(f"Validation complete. Total: {len(audit_records)}, Inconsistent: {inconsistent_count}")
    
    return len(audit_records), inconsistent_count

def main():
    """Main entry point for validator script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate A/B test summaries for statistical consistency")
    parser.add_argument("--input", required=True, help="Input JSON file with ABTestSummary objects")
    parser.add_argument("--output", required=True, help="Output JSON file for AuditRecord objects")
    
    args = parser.parse_args()
    
    total, inconsistent = run_validator(args.input, args.output)
    print(f"Processed {total} records, found {inconsistent} inconsistent.")

if __name__ == "__main__":
    main()