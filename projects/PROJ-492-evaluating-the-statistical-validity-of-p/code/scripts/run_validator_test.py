"""
Script to run validator unit tests and verify functionality.

This script validates that the inconsistency validator correctly:
1. Applies FR-004 thresholds (p-diff > 0.05, effect-size > 5%)
2. Flags sample-size mismatches
3. Excludes mismatched records from prevalence estimates
"""

import json
import sys
from pathlib import Path

from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import (
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    check_sample_size_consistency
)
from code.src.utils.logger import get_default_logger


def create_test_data():
    """Create test data for validation."""
    summaries = [
        ABTestSummary(
            url="http://example.com/good_test",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        ),
        ABTestSummary(
            url="http://example.com/bad_p_value",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        ),
        ABTestSummary(
            url="http://example.com/bad_effect_size",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        ),
        ABTestSummary(
            url="http://example.com/sample_size_mismatch",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=40,  # Extreme mismatch
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        ),
        ABTestSummary(
            url="http://example.com/both_bad",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=40,  # Extreme mismatch
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
    ]
    
    reconstructor_results = {
        "http://example.com/good_test": {"p_value": 0.04, "effect_size": 0.1},
        "http://example.com/bad_p_value": {"p_value": 0.10, "effect_size": 0.1},  # P-value diff > 0.05
        "http://example.com/bad_effect_size": {"p_value": 0.04, "effect_size": 0.15},  # Effect size diff > 5%
        "http://example.com/sample_size_mismatch": {"p_value": 0.04, "effect_size": 0.1},
        "http://example.com/both_bad": {"p_value": 0.10, "effect_size": 0.15}
    }
    
    return summaries, reconstructor_results


def main():
    """Run validation tests."""
    logger = get_default_logger()
    logger.info("Starting validator validation tests")
    
    try:
        # Create test data
        summaries, reconstructor_results = create_test_data()
        logger.info(f"Created {len(summaries)} test summaries")
        
        # Validate all summaries
        records = validate_all_summaries(summaries, reconstructor_results)
        logger.info(f"Validated {len(records)} summaries")
        
        # Check results
        inconsistent_count = sum(1 for r in records if r.is_inconsistent)
        logger.info(f"Inconsistent records: {inconsistent_count}")
        
        # Verify expected inconsistencies
        expected_inconsistent = [
            "http://example.com/bad_p_value",
            "http://example.com/bad_effect_size",
            "http://example.com/both_bad"
        ]
        
        actual_inconsistent = [r.url for r in records if r.is_inconsistent]
        
        for url in expected_inconsistent:
            if url not in actual_inconsistent:
                logger.error(f"Expected {url} to be inconsistent but it was not")
                return 1
        
        # Check sample size warnings
        sample_size_warnings = [
            r for r in records 
            if any("sample size" in w.lower() for w in r.data_quality_warnings)
        ]
        logger.info(f"Records with sample size warnings: {len(sample_size_warnings)}")
        
        expected_mismatch_urls = [
            "http://example.com/sample_size_mismatch",
            "http://example.com/both_bad"
        ]
        
        for url in expected_mismatch_urls:
            if url not in [r.url for r in sample_size_warnings]:
                logger.error(f"Expected {url} to have sample size warning but it was not found")
                return 1
        
        # Filter for prevalence
        filtered_records = filter_for_prevalence(records)
        logger.info(f"Records after prevalence filtering: {len(filtered_records)}")
        
        # Verify sample size mismatch records are excluded
        filtered_urls = [r.url for r in filtered_records]
        for url in expected_mismatch_urls:
            if url in filtered_urls:
                logger.error(f"Sample size mismatch record {url} should be excluded from prevalence")
                return 1
        
        # Write test report
        output_path = Path("output/validator_test_report.json")
        write_audit_report(records, output_path)
        logger.info(f"Test report written to {output_path}")
        
        # Write filtered report
        filtered_path = Path("output/validator_test_filtered.json")
        write_audit_report(filtered_records, filtered_path)
        logger.info(f"Filtered report written to {filtered_path}")
        
        logger.info("All validator tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"Validator test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())