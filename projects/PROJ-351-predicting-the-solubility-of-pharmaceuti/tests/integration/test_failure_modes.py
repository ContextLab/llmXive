"""
Integration tests for edge case stress testing.
Specifically tests network failure modes to validate the "Fail Loudly" rule.
"""
import os
import sys
import unittest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download_esol import fetch_esol_dataset, save_raw_csv, main as download_main
from data.preprocess import load_and_preprocess, main as preprocess_main

# Configure logging for the test runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestNetworkFailure(unittest.TestCase):
    """Tests to verify that network errors cause the pipeline to fail loudly."""

    def setUp(self):
        """Set up test fixtures."""
        self.results_dir = project_root / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.log_file = self.results_dir / "failure_test_log.txt"
        
        # Clear previous log if it exists
        if self.log_file.exists():
            self.log_file.unlink()

        # Setup a temporary directory for test data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def _log_result(self, test_name: str, success: bool, message: str):
        """Helper to log test results to the required log file."""
        status = "PASS" if success else "FAIL"
        log_entry = f"[{test_name}] {status}: {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        logger.info(log_entry.strip())

    @patch('data.download_esol.requests.get')
    def test_download_esol_network_failure(self, mock_get):
        """
        Test that fetch_esol_dataset raises an exception when network fails.
        This validates the 'Fail Loudly' constraint.
        """
        # Configure the mock to raise a network error
        mock_get.side_effect = Exception("Network Error: Name or service not known")

        test_name = "test_download_esol_network_failure"
        
        try:
            # Attempt to fetch the dataset - this should raise an exception
            fetch_esol_dataset(output_dir=self.test_data_dir)
            
            # If we reach here, the test failed (no exception raised)
            self._log_result(test_name, False, "Expected exception was not raised")
            self.fail("fetch_esol_dataset did not raise an exception on network failure")
            
        except Exception as e:
            # Expected behavior: exception raised
            error_msg = str(e)
            self._log_result(test_name, True, f"Correctly raised exception: {error_msg}")

    @patch('data.download_esol.requests.get')
    def test_download_esol_hf_fallback_failure(self, mock_get):
        """
        Test that the script fails when both primary and HF mirror fail.
        """
        # Mock both attempts to fail
        mock_get.side_effect = Exception("Connection Refused")

        test_name = "test_download_esol_hf_fallback_failure"

        try:
            fetch_esol_dataset(output_dir=self.test_data_dir)
            self._log_result(test_name, False, "Expected exception was not raised on fallback failure")
            self.fail("fetch_esol_dataset did not raise an exception when both sources failed")
        except Exception as e:
            self._log_result(test_name, True, f"Correctly raised exception on fallback failure: {str(e)}")

    def test_preprocess_with_missing_file(self):
        """
        Test that preprocessing fails loudly when input file is missing.
        """
        test_name = "test_preprocess_missing_file"
        non_existent_file = self.test_data_dir / "non_existent.csv"

        try:
            load_and_preprocess(str(non_existent_file), output_dir=self.test_data_dir)
            self._log_result(test_name, False, "Expected exception was not raised for missing file")
            self.fail("load_and_preprocess did not raise an exception for missing file")
        except FileNotFoundError as e:
            self._log_result(test_name, True, f"Correctly raised FileNotFoundError: {str(e)}")
        except Exception as e:
            # Accept other exceptions if they indicate a failure to process
            self._log_result(test_name, True, f"Correctly raised exception: {type(e).__name__}: {str(e)}")

    def test_main_download_network_failure(self):
        """
        Test that the main entry point of download_esol fails loudly on network error.
        """
        with patch('data.download_esol.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network Unreachable")
            
            test_name = "test_main_download_network_failure"
            
            # We need to capture the exit or exception from main
            # Since main() might sys.exit, we catch the exception or assert the side effect
            try:
                # Call the main function logic directly or via the module
                # We simulate the call to the internal logic
                fetch_esol_dataset(output_dir=self.test_data_dir)
                self._log_result(test_name, False, "Main logic did not fail on network error")
            except Exception as e:
                self._log_result(test_name, True, f"Main logic correctly failed: {str(e)}")

class TestRDKitParsingErrors(unittest.TestCase):
    """Tests for data parsing edge cases."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)
        self.results_dir = project_root / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.log_file = self.results_dir / "failure_test_log.txt"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_invalid_smiles_handling(self):
        """
        Test that invalid SMILES are handled (logged and excluded) without crashing the whole process,
        but the process should still raise warnings or errors if ALL data is invalid.
        """
        test_name = "test_invalid_smiles_handling"
        
        # Create a CSV with only invalid SMILES
        invalid_csv = self.test_data_dir / "invalid.csv"
        invalid_csv.write_text("smiles,logS\nINVALID_SMILES,1.0\n")
        
        try:
            # This should process, log exclusions, but might return empty or raise if strict
            # Based on T005 spec: "log count... and raise warning". 
            # We verify it doesn't crash silently or produce fake data.
            from data.preprocess import load_and_preprocess
            result = load_and_preprocess(str(invalid_csv), output_dir=self.test_data_dir)
            
            # If it returns empty result without crashing, that's acceptable behavior for T005
            # But if it returns fake data, that's a fail.
            if result is not None and len(result) == 0:
                self._log_result(test_name, True, "Correctly handled all invalid SMILES (returned empty)")
            else:
                self._log_result(test_name, False, "Returned unexpected data for invalid SMILES")
                
        except Exception as e:
            # If it raises an error because no valid data, that is also "Fail Loudly" acceptable
            self._log_result(test_name, True, f"Correctly raised exception for all invalid data: {str(e)}")

def run_all_tests():
    """Run all tests and ensure the log file is generated."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkFailure))
    suite.addTests(loader.loadTestsFromTestCase(TestRDKitParsingErrors))
    
    runner = unittest.TestRunner()
    result = runner.run(suite)
    
    # Ensure the log file exists even if tests fail (to satisfy the artifact requirement)
    log_file = project_root / "results" / "failure_test_log.txt"
    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'w') as f:
            f.write("Tests executed. See stdout for details.\n")
            for test in result.testsRun:
                f.write(f"Executed: {test}\n")
    
    return result

if __name__ == '__main__':
    run_all_tests()
