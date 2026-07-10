"""
Validator module for T025: Implement inconsistency validator applying FR-004 thresholds.
Also implements T025b logic: flagging missing baseline conversion rates per FR-012.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.reconstructor import ReconstructionResult
import numpy as np

logger = get_default_logger(__name__)

# FR-004 Thresholds
P_VALUE_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_RELATIVE_THRESHOLD = 0.05  # 5%

def validate_single_record(summary: ABTestSummary, reconstructed: ReconstructionResult) -> AuditRecord:
    """
    Validate a single ABTestSummary against its reconstructed statistical values.
    Implements FR-004 thresholds and FR-012 missing baseline flagging.
    """
    notes_parts = []
    data_quality_warning = None
    is_inconsistent = False

    # FR-012: Check for missing baseline conversion rate
    if summary.conversion_rate_control is None:
        notes_parts.append("missing baseline conversion rate")
        data_quality_warning = "Missing baseline conversion rate as per FR-012"
    
    if summary.conversion_rate_treatment is None:
        notes_parts.append("missing treatment conversion rate")
        if data_quality_warning:
            data_quality_warning += "; Missing treatment conversion rate"
        else:
            data_quality_warning = "Missing treatment conversion rate"

    # Check for sample size mismatch (FR-004b)
    if summary.sample_size_control != summary.sample_size_treatment:
        notes_parts.append("sample size mismatch between control and treatment")
        # Per FR-004b, this is a data quality warning but not necessarily an inconsistency flag yet
        if not data_quality_warning:
            data_quality_warning = "Sample size mismatch detected"
        else:
            data_quality_warning += "; Sample size mismatch"

    # Compare reported vs reconstructed p-values (FR-004)
    if reconstructed.reported_p_value is not None and reconstructed.reconstructed_p_value is not None:
        p_diff = abs(reconstructed.reported_p_value - reconstructed.reconstructed_p_value)
        if p_diff > P_VALUE_DIFF_THRESHOLD:
            notes_parts.append(f"p-value discrepancy: reported {reconstructed.reported_p_value:.4f}, reconstructed {reconstructed.reconstructed_p_value:.4f}")
            is_inconsistent = True

    # Compare reported vs reconstructed effect sizes (FR-004)
    if reconstructed.reported_effect_size is not None and reconstructed.reconstructed_effect_size is not None:
        reported = reconstructed.reported_effect_size
        reconstructed_eff = reconstructed.reconstructed_effect_size
        if abs(reported) > 0:
            rel_diff = abs(reported - reconstructed_eff) / abs(reported)
            if rel_diff > EFFECT_SIZE_RELATIVE_THRESHOLD:
                notes_parts.append(f"effect size discrepancy: reported {reported:.4f}, reconstructed {reconstructed_eff:.4f}")
                is_inconsistent = True
        else:
            # If reported is 0 but reconstructed is not, that's a discrepancy
            if abs(reconstructed_eff) > 0:
                notes_parts.append(f"effect size discrepancy: reported 0, reconstructed {reconstructed_eff:.4f}")
                is_inconsistent = True

    notes = "; ".join(notes_parts) if notes_parts else None

    return AuditRecord(
        url=summary.url,
        domain=summary.domain,
        is_inconsistent=is_inconsistent,
        notes=notes,
        data_quality_warning=data_quality_warning,
        publication_year=summary.publication_year,
        test_type=summary.test_type
    )

def validate_all_records(
    summaries: List[ABTestSummary],
    reconstructed_list: List[ReconstructionResult]
) -> List[AuditRecord]:
    """
    Validate a batch of summaries against their reconstructed values.
    """
    if len(summaries) != len(reconstructed_list):
        raise ValueError(f"Number of summaries ({len(summaries)}) does not match number of reconstructions ({len(reconstructed_list)})")

    audit_records = []
    for summary, reconstructed in zip(summaries, reconstructed_list):
        record = validate_single_record(summary, reconstructed)
        audit_records.append(record)
        if record.notes:
            logger.info(f"Validation notes for {summary.url}: {record.notes}")
        if record.data_quality_warning:
            logger.warning(f"Data quality warning for {summary.url}: {record.data_quality_warning}")

    return audit_records

def run_validation_pipeline(
    summaries: List[ABTestSummary],
    output_path: Optional[Path] = None
) -> List[AuditRecord]:
    """
    Run the full validation pipeline on a list of summaries.
    Optionally writes results to output_path.
    """
    from code.src.audit.reconstructor import reconstruct_all
    
    reconstructed_list = reconstruct_all(summaries)
    audit_records = validate_all_records(summaries, reconstructed_list)

    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([r.model_dump() for r in audit_records], f, indent=2)
        logger.info(f"Audit records written to {output_path}")

    return audit_records

def main():
    """
    Main entry point for validator script.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Validate AB test summaries")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON with summaries")
    parser.add_argument("--output", type=str, default="output/audit_report.json", help="Path to output JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    import json
    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    summaries = [ABTestSummary(**item) for item in summaries_data]
    audit_records = run_validation_pipeline(summaries, output_path)

    inconsistent_count = sum(1 for r in audit_records if r.is_inconsistent)
    logger.info(f"Validation complete. Total: {len(audit_records)}, Inconsistent: {inconsistent_count}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())