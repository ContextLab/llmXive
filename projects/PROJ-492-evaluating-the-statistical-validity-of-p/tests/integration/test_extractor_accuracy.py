"""
Integration test for T036: FR-002 Verification.
Asserts that extracted fields exist for > 95% of valid pages.
"""
import json
import logging
import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed

logger = get_default_logger()

# Required fields that must be present in a valid ABTestSummary
# Based on the data model and extraction logic
REQUIRED_FIELDS = [
    'url',
    'domain',
    'test_type',
    'outcome_type',
    'sample_size_control',
    'sample_size_treatment',
    'baseline_conversion_rate',
    'treatment_conversion_rate',
    'reported_p_value',
    'reported_effect_size',
    'outcome_direction',
    'statistical_significance'
]

def load_extracted_summaries(filepath: Path) -> List[Dict[str, Any]]:
    """Load extracted summaries from JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Extracted summaries file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'summaries' in data:
        return data['summaries']
    else:
        raise ValueError(f"Unexpected format in {filepath}")

def calculate_field_coverage(
    summaries: List[Dict[str, Any]],
    required_fields: List[str]
) -> Dict[str, float]:
    """
    Calculate the percentage of records that have all required fields.
    Returns a dict with coverage metrics.
    """
    total_records = len(summaries)
    if total_records == 0:
        return {
            'total_records': 0,
            'records_with_all_fields': 0,
            'coverage_percentage': 0.0
        }

    records_with_all_fields = 0
    
    for record in summaries:
        has_all_fields = True
        for field in required_fields:
            if field not in record or record[field] is None:
                has_all_fields = False
                break
        
        if has_all_fields:
            records_with_all_fields += 1

    coverage_percentage = (records_with_all_fields / total_records) * 100.0
    
    return {
        'total_records': total_records,
        'records_with_all_fields': records_with_all_fields,
        'coverage_percentage': coverage_percentage
    }

def run_extractor_on_synthetic_data() -> Path:
    """
    Run the extractor on the synthetic validation dataset.
    This simulates the pipeline flow for testing purposes.
    """
    # Set seed for reproducibility
    set_rng_seed(42)
    
    # Paths
    synthetic_csv = PROJECT_ROOT / 'data' / 'synthetic' / 'synthetic_validation.csv'
    extracted_json = PROJECT_ROOT / 'output' / 'extracted_summaries.json'
    
    # Ensure output directory exists
    extracted_json.parent.mkdir(parents=True, exist_ok=True)
    
    # Run extraction
    logger.info(f"Running extractor on {synthetic_csv}")
    summaries = extract_all(synthetic_csv)
    
    # Write results
    write_summaries_to_json(summaries, extracted_json)
    
    logger.info(f"Extracted {len(summaries)} summaries to {extracted_json}")
    return extracted_json

class TestExtractorAccuracy(unittest.TestCase):
    """
    Test suite for T036: FR-002 Verification.
    Verifies that extracted fields exist for > 95% of valid pages.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_default_logger()
        self.required_fields = REQUIRED_FIELDS
        self.threshold = 95.0  # 95% coverage threshold

    def test_extractor_coverage(self):
        """
        Main test: Assert that extracted fields exist for > 95% of valid pages.
        
        This test:
        1. Runs the extractor on the synthetic validation dataset
        2. Loads the extracted summaries
        3. Calculates the percentage of records with all required fields
        4. Asserts coverage is > 95%
        """
        self.logger.info("Starting T036: FR-002 Verification test")
        
        # Run extractor
        try:
            extracted_path = run_extractor_on_synthetic_data()
        except Exception as e:
            self.logger.error(f"Extractor failed: {e}")
            self.fail(f"Extractor execution failed: {e}")
        
        # Load extracted summaries
        try:
            summaries = load_extracted_summaries(extracted_path)
        except Exception as e:
            self.logger.error(f"Failed to load extracted summaries: {e}")
            self.fail(f"Failed to load extracted summaries: {e}")
        
        # Calculate coverage
        coverage = calculate_field_coverage(summaries, self.required_fields)
        
        self.logger.info(f"Coverage Results:")
        self.logger.info(f"  Total records: {coverage['total_records']}")
        self.logger.info(f"  Records with all fields: {coverage['records_with_all_fields']}")
        self.logger.info(f"  Coverage percentage: {coverage['coverage_percentage']:.2f}%")
        self.logger.info(f"  Threshold: {self.threshold}%")
        
        # Assert coverage meets threshold
        self.assertGreater(
            coverage['total_records'], 0,
            "No records were extracted. Check if synthetic dataset exists."
        )
        
        self.assertGreaterEqual(
            coverage['coverage_percentage'], self.threshold,
            f"Field coverage ({coverage['coverage_percentage']:.2f}%) is below "
            f"the required threshold ({self.threshold}%). "
            f"Only {coverage['records_with_all_fields']} of "
            f"{coverage['total_records']} records have all required fields."
        )
        
        self.logger.info("✓ T036: FR-002 Verification PASSED")

    def test_individual_field_presence(self):
        """
        Additional test: Verify each required field is present in at least some records.
        This helps identify which fields might be problematic.
        """
        # Run extractor if needed
        extracted_path = PROJECT_ROOT / 'output' / 'extracted_summaries.json'
        if not extracted_path.exists():
            extracted_path = run_extractor_on_synthetic_data()
        
        summaries = load_extracted_summaries(extracted_path)
        
        if not summaries:
            self.skipTest("No summaries to test")
        
        # Check each field
        field_presence = {}
        for field in self.required_fields:
            count = sum(1 for r in summaries if field in r and r[field] is not None)
            field_presence[field] = count / len(summaries) * 100
        
        self.logger.info("Individual field presence:")
        for field, percentage in field_presence.items():
            self.logger.info(f"  {field}: {percentage:.2f}%")
        
        # Assert no field is completely missing
        for field, percentage in field_presence.items():
            self.assertGreater(
                percentage, 0,
                f"Field '{field}' is missing from all records."
            )

    def test_empty_summaries_handling(self):
        """Test that the coverage calculation handles empty input gracefully."""
        coverage = calculate_field_coverage([], self.required_fields)
        
        self.assertEqual(coverage['total_records'], 0)
        self.assertEqual(coverage['records_with_all_fields'], 0)
        self.assertEqual(coverage['coverage_percentage'], 0.0)

def main():
    """Run the test suite."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExtractorAccuracy)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()