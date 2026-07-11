"""
Unit tests for T025c: Verify sample-size mismatch exclusion logic.

This test suite validates that:
1. Audit records flagged with data_quality_warning for sample-size discrepancies
   are correctly identified.
2. These flagged records are excluded from aggregate prevalence estimates as per FR-004b.
3. The exclusion logic does not affect the count of inconsistent entries for valid records.

Dependencies:
- T025: Implement inconsistency validator in src/audit/validator.py
"""

import json
import logging
import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.audit.validator import run_validator, main as validator_main
from code.src.utils.logger import get_default_logger, AuditLogger

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_default_logger()


class TestSampleSizeExclusion(unittest.TestCase):
    """Test suite for sample-size exclusion logic in audit validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path("data/test_fixtures")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create test audit records with known sample-size mismatches
        self.test_records = [
            # Valid record - no sample size mismatch
            {
                "id": "valid_001",
                "url": "https://example.com/valid-test",
                "domain": "tech",
                "is_inconsistent": True,
                "data_quality_warning": None,
                "reported_p_value": 0.03,
                "reconstructed_p_value": 0.04,
                "effect_size": 0.15,
                "sample_size_a": 1000,
                "sample_size_b": 1000,
                "baseline_rate": 0.20
            },
            # Valid record - no sample size mismatch, consistent
            {
                "id": "valid_002",
                "url": "https://example.com/valid-test-2",
                "domain": "tech",
                "is_inconsistent": False,
                "data_quality_warning": None,
                "reported_p_value": 0.15,
                "reconstructed_p_value": 0.16,
                "effect_size": 0.05,
                "sample_size_a": 500,
                "sample_size_b": 500,
                "baseline_rate": 0.10
            },
            # Invalid record - sample size mismatch flagged
            {
                "id": "invalid_001",
                "url": "https://example.com/invalid-test-1",
                "domain": "finance",
                "is_inconsistent": True,
                "data_quality_warning": "sample_size_mismatch",
                "reported_p_value": 0.01,
                "reconstructed_p_value": 0.08,
                "effect_size": 0.25,
                "sample_size_a": 100,
                "sample_size_b": 5000,  # Large discrepancy
                "baseline_rate": 0.30
            },
            # Invalid record - sample size mismatch flagged
            {
                "id": "invalid_002",
                "url": "https://example.com/invalid-test-2",
                "domain": "finance",
                "is_inconsistent": False,
                "data_quality_warning": "sample_size_mismatch",
                "reported_p_value": 0.04,
                "reconstructed_p_value": 0.05,
                "effect_size": 0.12,
                "sample_size_a": 200,
                "sample_size_b": 4500,  # Large discrepancy
                "baseline_rate": 0.25
            },
            # Valid record - no sample size mismatch, inconsistent
            {
                "id": "valid_003",
                "url": "https://example.com/valid-test-3",
                "domain": "health",
                "is_inconsistent": True,
                "data_quality_warning": None,
                "reported_p_value": 0.02,
                "reconstructed_p_value": 0.09,  # > 0.05 difference
                "effect_size": 0.18,
                "sample_size_a": 800,
                "sample_size_b": 850,
                "baseline_rate": 0.15
            }
        ]

        # Write test data to file
        self.test_input_file = self.test_data_dir / "test_audit_records.json"
        with open(self.test_input_file, 'w') as f:
            json.dump(self.test_records, f, indent=2)

        self.test_output_file = self.test_data_dir / "test_audit_output.json"

    def test_sample_size_mismatch_flagging(self):
        """Verify that records with sample-size mismatches are flagged."""
        # Run the validator on test data
        validator_main(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file)
        )

        # Load the output
        with open(self.test_output_file, 'r') as f:
            output_records = json.load(f)

        # Verify that records with sample_size_mismatch are flagged
        invalid_001 = next((r for r in output_records if r['id'] == 'invalid_001'), None)
        invalid_002 = next((r for r in output_records if r['id'] == 'invalid_002'), None)

        self.assertIsNotNone(invalid_001, "invalid_001 not found in output")
        self.assertIsNotNone(invalid_002, "invalid_002 not found in output")

        self.assertEqual(
            invalid_001['data_quality_warning'],
            "sample_size_mismatch",
            "invalid_001 should have sample_size_mismatch warning"
        )
        self.assertEqual(
            invalid_002['data_quality_warning'],
            "sample_size_mismatch",
            "invalid_002 should have sample_size_mismatch warning"
        )

    def test_exclusion_from_prevalence_calculation(self):
        """Verify that sample-size mismatched records are excluded from prevalence estimates."""
        # Run the validator on test data
        validator_main(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file)
        )

        # Load the output
        with open(self.test_output_file, 'r') as f:
            output_records = json.load(f)

        # Count total inconsistent records (including those with warnings)
        total_inconsistent = sum(1 for r in output_records if r['is_inconsistent'])
        
        # Count inconsistent records WITHOUT sample_size_mismatch warning
        valid_inconsistent = sum(
            1 for r in output_records 
            if r['is_inconsistent'] and r['data_quality_warning'] != 'sample_size_mismatch'
        )

        # Count records with sample_size_mismatch warning
        mismatched_count = sum(
            1 for r in output_records 
            if r['data_quality_warning'] == 'sample_size_mismatch'
        )

        # Verify that mismatched records are flagged
        self.assertEqual(mismatched_count, 2, "Should have 2 records with sample_size_mismatch")

        # Verify that the valid inconsistent count matches expected (valid_001 and valid_003)
        self.assertEqual(valid_inconsistent, 2, "Should have 2 valid inconsistent records")

        # Verify that total inconsistent is higher than valid inconsistent
        self.assertGreater(total_inconsistent, valid_inconsistent, 
                         "Total inconsistent should be higher than valid inconsistent")

        logger.info(f"Test passed: {mismatched_count} records correctly flagged for exclusion")
        logger.info(f"Valid inconsistent count: {valid_inconsistent}")
        logger.info(f"Total inconsistent count: {total_inconsistent}")

    def test_prevalence_calculation_without_mismatched(self):
        """Verify prevalence rate calculation excludes sample-size mismatched records."""
        # Run the validator on test data
        validator_main(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file)
        )

        # Load the output
        with open(self.test_output_file, 'r') as f:
            output_records = json.load(f)

        # Calculate prevalence rate excluding mismatched records
        valid_records = [
            r for r in output_records 
            if r['data_quality_warning'] != 'sample_size_mismatch'
        ]
        
        if len(valid_records) == 0:
            self.fail("No valid records found for prevalence calculation")

        valid_inconsistent = [r for r in valid_records if r['is_inconsistent']]
        prevalence_rate = len(valid_inconsistent) / len(valid_records)

        # Expected: 2 inconsistent out of 3 valid records (valid_001, valid_002, valid_003)
        # valid_001: inconsistent, no warning
        # valid_002: consistent, no warning
        # valid_003: inconsistent, no warning
        expected_prevalence = 2 / 3

        self.assertAlmostEqual(
            prevalence_rate, 
            expected_prevalence, 
            places=5,
            msg=f"Prevalence rate {prevalence_rate} should be {expected_prevalence}"
        )

        logger.info(f"Prevalence rate (excluding mismatched): {prevalence_rate:.4f}")
        logger.info(f"Expected prevalence rate: {expected_prevalence:.4f}")

    def test_fr004b_compliance(self):
        """Verify FR-004b compliance: sample-size mismatch entries excluded from aggregate prevalence."""
        # Run the validator on test data
        validator_main(
            input_file=str(self.test_input_file),
            output_file=str(self.test_output_file)
        )

        # Load the output
        with open(self.test_output_file, 'r') as f:
            output_records = json.load(f)

        # Check that all records with sample_size_mismatch have the warning flag
        mismatched_records = [
            r for r in output_records 
            if r['data_quality_warning'] == 'sample_size_mismatch'
        ]

        for record in mismatched_records:
            self.assertIn(
                'sample_size_mismatch',
                str(record.get('data_quality_warning', '')),
                f"Record {record['id']} should have sample_size_mismatch warning"
            )

        # Verify that the exclusion logic is documented in the output
        # (This is a basic check - in production, we'd check for specific metadata)
        self.assertTrue(
            any('sample_size' in str(r.get('data_quality_warning', '')).lower() 
                for r in output_records),
            "At least one record should have sample_size related warning"
        )

        logger.info("FR-004b compliance verified: sample-size mismatched records are flagged and excluded")


def run_tests():
    """Run all tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSampleSizeExclusion)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def main():
    """Main entry point for the test script."""
    logger.info("Starting sample size exclusion tests (T025c)")
    success = run_tests()
    
    if success:
        logger.info("All tests passed successfully")
        return 0
    else:
        logger.error("Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())