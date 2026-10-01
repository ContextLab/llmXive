"""
Unit tests for the compliance verification module.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_check import (
    verify_checksums,
    verify_fail_loudly,
    verify_state_management,
    verify_reproducibility,
    verify_artifact_hashes,
    verify_data_ingestion,
    verify_baseline_logic,
    verify_scope_check,
    verify_power_analysis,
    verify_fidelity_threshold,
    run_compliance_check
)
from utils.error_codes import ErrorCode


class TestComplianceVerification(unittest.TestCase):
    """Test cases for compliance verification functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_verify_checksums_no_state_file(self):
        """Test verify_checksums when state file is missing."""
        success, message = verify_checksums()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_fail_loudly(self):
        """Test that fail-loudly error codes are defined."""
        success, message = verify_fail_loudly()
        self.assertTrue(success)
        self.assertIn("verified", message.lower())

    def test_verify_state_management_no_dir(self):
        """Test verify_state_management when state directory is missing."""
        success, message = verify_state_management()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_reproducibility_no_test(self):
        """Test verify_reproducibility when test file is missing."""
        # Create a dummy test file without the required function
        os.makedirs("tests", exist_ok=True)
        with open("tests/test_model.py", 'w') as f:
            f.write("# Dummy test file\n")
        
        success, message = verify_reproducibility()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_artifact_hashes_no_model(self):
        """Test verify_artifact_hashes when model artifact is missing."""
        success, message = verify_artifact_hashes()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_data_ingestion_no_file(self):
        """Test verify_data_ingestion when ingest file is missing."""
        success, message = verify_data_ingestion()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_baseline_logic_no_file(self):
        """Test verify_baseline_logic when baseline file is missing."""
        success, message = verify_baseline_logic()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_scope_check_no_file(self):
        """Test verify_scope_check when train file is missing."""
        success, message = verify_scope_check()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_power_analysis_no_file(self):
        """Test verify_power_analysis when train file is missing."""
        success, message = verify_power_analysis()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_verify_fidelity_threshold_no_file(self):
        """Test verify_fidelity_threshold when viz file is missing."""
        success, message = verify_fidelity_threshold()
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_run_compliance_check_structure(self):
        """Test that run_compliance_check returns expected structure."""
        results = run_compliance_check()
        
        self.assertIn("constitutional_principles", results)
        self.assertIn("specification_requirements", results)
        self.assertIn("fidelity_requirements", results)
        self.assertIn("overall_status", results)
        self.assertIn("issues", results)
        
        self.assertIn("COMPLIANT", results["overall_status"])
        self.assertIn("NON_COMPLIANT", results["overall_status"])

    def test_error_codes_exist(self):
        """Test that required error codes exist."""
        required_codes = [
            "DATA_SOURCE_MISSING",
            "INVALID_DATA_SCHEMA",
            "MISSING_TEMP_COORDS",
            "LOW_DATA_DENSITY",
            "API_RATE_LIMIT_EXCEEDED",
            "INSUFFICIENT_POWER",
            "INVALID_SCOPE",
            "RESOURCE_LIMIT_EXCEEDED",
            "NO_SIGNIFICANT_IMPROVEMENT",
            "LOW_DATA_FIDELITY",
            "DATA_SCHEMA_MISMATCH",
            "TEMPERATURE_RANGE_VIOLATION",
            "COMPOSITION_SUM_ERROR",
            "POTENTIAL_MEMORY_LEAK",
            "MISSING_GROUND_TRUTH",
            "LOW_RESOLUTION_PLOT",
            "DATA_INTEGRITY_VIOLATION"
        ]
        
        for code_name in required_codes:
            self.assertTrue(hasattr(ErrorCode, code_name), 
                          f"Error code {code_name} not found in ErrorCode enum")


if __name__ == "__main__":
    unittest.main()
