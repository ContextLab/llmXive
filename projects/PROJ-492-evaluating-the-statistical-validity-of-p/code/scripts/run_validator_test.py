"""
Script to run the validator on sample data and generate the audit report.
This script demonstrates the functionality of T025.
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import validate_all_summaries, write_audit_report, filter_for_prevalence
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def main():
    input_path = Path(__file__).parent.parent / "data" / "raw" / "sample_summaries_for_validation.json"
    output_path = Path(__file__).parent.parent / "output" / "audit_report.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load summaries
    with open(input_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**s) for s in summaries_data]

    logger.info(f"Loaded {len(summaries)} summaries for validation.")

    # Validate
    records = validate_all_summaries(summaries)

    # Write report
    write_audit_report(records, output_path)

    # Demonstrate FR-004b: Filter for prevalence
    prevalence_records = filter_for_prevalence(records)
    
    logger.info(f"Total records: {len(records)}")
    logger.info(f"Records for prevalence (excluding sample mismatch): {len(prevalence_records)}")
    
    mismatch_count = sum(1 for r in records if r.sample_size_mismatch)
    logger.info(f"Excluded {mismatch_count} records due to sample size mismatch.")

    logger.info("Validation complete. Output written to output/audit_report.json")

if __name__ == "__main__":
    main()