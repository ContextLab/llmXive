"""
Integration test for FR-002 Verification: Extracted fields exist for > 95% of valid pages.

This test loads the extracted summaries from data/processed/extracted_summaries.json
and verifies that required fields are present in at least 95% of valid pages.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.logger import get_default_logger, get_error_message

logger = get_default_logger(__name__)

# Define required fields based on ABTestSummary model
REQUIRED_FIELDS = {
    'url',
    'domain',
    'baseline_conversion_rate',
    'treatment_conversion_rate',
    'baseline_sample_size',
    'treatment_sample_size',
    'p_value',
    'effect_size',
    'test_type',
    'outcome_type',
    'is_significant'
}

def load_extracted_summaries(file_path: Path) -> List[Dict[str, Any]]:
    """Load extracted summaries from JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Extracted summaries file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'summaries' in data:
        return data['summaries']
    else:
        raise ValueError("Unexpected format in extracted summaries file")

def count_valid_pages(summaries: List[Dict[str, Any]]) -> int:
    """Count pages that have at least one required field (considered 'valid')."""
    valid_count = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        # A page is considered 'valid' if it has at least one of the required fields
        if any(field in summary for field in REQUIRED_FIELDS):
            valid_count += 1
    return valid_count

def count_complete_records(summaries: List[Dict[str, Any]], required_fields: Set[str]) -> int:
    """Count records that have ALL required fields."""
    complete_count = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        if required_fields.issubset(summary.keys()):
            complete_count += 1
    return complete_count

def calculate_field_coverage(summaries: List[Dict[str, Any]], required_fields: Set[str]) -> Dict[str, float]:
    """Calculate coverage for each required field."""
    field_counts = {field: 0 for field in required_fields}
    total_valid = 0
    
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        # Only count if it's a valid page (has at least one required field)
        if any(field in summary for field in required_fields):
            total_valid += 1
            for field in required_fields:
                if field in summary:
                    field_counts[field] += 1
    
    coverage = {}
    for field, count in field_counts.items():
        coverage[field] = (count / total_valid * 100) if total_valid > 0 else 0.0
    
    return coverage, total_valid

def test_extractor_field_coverage():
    """
    FR-002 Verification: Extracted fields exist for > 95% of valid pages.
    
    This test:
    1. Loads extracted summaries from data/processed/extracted_summaries.json
    2. Identifies valid pages (those with at least one required field)
    3. Calculates the percentage of valid pages that have ALL required fields
    4. Asserts that this percentage is > 95%
    """
    # Path to extracted summaries
    summaries_path = project_root / "data" / "processed" / "extracted_summaries.json"
    
    try:
        logger.info(f"Loading extracted summaries from: {summaries_path}")
        summaries = load_extracted_summaries(summaries_path)
        logger.info(f"Loaded {len(summaries)} summaries")
    except FileNotFoundError as e:
        logger.error(f"Failed to load summaries: {e}")
        # If no summaries exist, we cannot verify coverage
        # This might indicate that previous steps (T020) haven't run yet
        raise RuntimeError(
            f"Cannot verify FR-002: {e}. "
            "Please ensure T020 (extractor) has been executed successfully."
        )
    
    if len(summaries) == 0:
        raise RuntimeError("No summaries found to verify field coverage")
    
    # Count valid pages
    valid_pages = count_valid_pages(summaries)
    logger.info(f"Found {valid_pages} valid pages out of {len(summaries)} total")
    
    if valid_pages == 0:
        raise RuntimeError("No valid pages found - all pages may be malformed")
    
    # Count complete records
    complete_records = count_complete_records(summaries, REQUIRED_FIELDS)
    logger.info(f"Found {complete_records} complete records with all required fields")
    
    # Calculate coverage percentage
    coverage_percentage = (complete_records / valid_pages) * 100
    logger.info(f"Field coverage: {coverage_percentage:.2f}% ({complete_records}/{valid_pages})")
    
    # Calculate per-field coverage for reporting
    field_coverage, total_valid = calculate_field_coverage(summaries, REQUIRED_FIELDS)
    logger.info("Per-field coverage:")
    for field, coverage in sorted(field_coverage.items()):
        logger.info(f"  {field}: {coverage:.2f}%")
    
    # Assert coverage > 95%
    threshold = 95.0
    if coverage_percentage >= threshold:
        logger.info(f"✓ FR-002 PASSED: Field coverage ({coverage_percentage:.2f}%) exceeds threshold ({threshold}%)")
        return True
    else:
        error_msg = (
            f"FR-002 FAILED: Field coverage ({coverage_percentage:.2f}%) is below threshold ({threshold}%). "
            f"Complete records: {complete_records}/{valid_pages}. "
            f"Per-field coverage: {field_coverage}"
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)

def main():
    """Main entry point for the test."""
    try:
        success = test_extractor_field_coverage()
        if success:
            logger.info("Test completed successfully")
            return 0
        else:
            logger.error("Test failed")
            return 1
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
