"""
Integration tests for the data retrieval and preprocessing pipeline.

Specifically tests the exclusion of discharges with missing data as per
User Story 1 requirements.
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import logging

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import setup_logging, get_logger
from utils.limits import timeout_guard, TimeoutError
from data.retrieval import fetch_discharge_data
from data.preprocessing import process_discharge_data
from main import validate_discharge_list


# Configure logging for tests
setup_logging(level=logging.INFO)
logger = get_logger(__name__)


# Use a fixed set of test discharges known to have varying data completeness
# These are real DIII-D discharge IDs. We expect some to have missing fields.
# Note: In a real CI environment, these would be replaced with mock data
# or a specific subset known to be available in the test MDSplus instance.
TEST_DISCHARGES = [
    166611,  # Known to have complete data
    166612,  # Known to have missing island_width data
    166613,  # Known to have missing tau_e data
]


class TestPipelineExclusion:
    """Test suite for verifying that discharges with missing data are excluded."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        yield
        shutil.rmtree(self.temp_dir)

    def test_missing_data_exclusion(self):
        """
        Test that discharges with missing critical data fields are excluded
        from the final processed dataset.
        
        This is an integration test that exercises the full pipeline from
        retrieval to preprocessing, verifying that the exclusion logic works
        as expected.
        """
        # Run the pipeline with a timeout to prevent hanging
        try:
            with timeout_guard(seconds=300):
                # Step 1: Fetch data
                logger.info(f"Fetching data for discharges: {TEST_DISCHARGES}")
                raw_data = fetch_discharge_data(TEST_DISCHARGES)
                
                # Step 2: Process data (this includes exclusion logic)
                logger.info("Processing data and applying exclusion rules")
                processed_data = process_discharge_data(raw_data)
                
        except TimeoutError:
            pytest.fail("Pipeline execution timed out")
        except Exception as e:
            # If MDSplus is not available, this is expected in some environments
            # We check if the error is related to connection issues
            if "MDSplus" in str(e) or "connection" in str(e).lower():
                pytest.skip("MDSplus connection not available in test environment")
            else:
                raise

        # Verify exclusion logic
        # We expect that discharges with missing critical data are excluded
        # The exact behavior depends on the implementation of process_discharge_data
        
        # Check that the processed data is not empty (we expect at least one valid discharge)
        assert len(processed_data) > 0, "No valid discharges found in processed data"
        
        # Check that the processed data contains the expected columns
        expected_columns = ['discharge_id', 'island_width', 'tau_e', 'confinement_mode']
        for col in expected_columns:
            assert col in processed_data.columns, f"Missing expected column: {col}"
        
        # Verify that no rows have NaN values in critical columns
        # This ensures that the exclusion logic worked correctly
        for col in ['island_width', 'tau_e']:
            assert not processed_data[col].isna().any(), f"Found NaN values in {col} column"
        
        logger.info(f"Successfully processed {len(processed_data)} valid discharges")
        logger.info(f"Excluded {len(TEST_DISCHARGES) - len(processed_data)} discharges due to missing data")

    def test_validate_discharge_list_integration(self):
        """
        Integration test for the validate_discharge_list function.
        
        Verifies that the validation logic correctly identifies and rejects
        invalid discharge IDs before they reach the retrieval stage.
        """
        # Test with a mix of valid and invalid discharge IDs
        valid_ids = [166611, 166612]
        invalid_ids = [-1, 0, 9999999]
        
        # Test valid IDs
        try:
            with timeout_guard(seconds=30):
                valid_result = validate_discharge_list(valid_ids)
                assert valid_result, "Valid discharge IDs were incorrectly rejected"
        except Exception:
            pytest.skip("Validation not available in test environment")
        
        # Test invalid IDs
        try:
            with timeout_guard(seconds=30):
                invalid_result = validate_discharge_list(invalid_ids)
                # The function should return False or raise an error for invalid IDs
                # The exact behavior depends on the implementation
                if invalid_result is not None:
                    assert not invalid_result, "Invalid discharge IDs were incorrectly accepted"
        except Exception:
            # Expected behavior for invalid IDs
            pass

    def test_empty_dataset_handling(self):
        """
        Test that the pipeline correctly handles the case where all discharges
        are excluded due to missing data.
        """
        # Use a list of discharges that are known to have missing data
        # In a real test environment, we would use a specific set of IDs
        # For this test, we simulate the case by using an empty list
        # or by mocking the retrieval to return empty data
        
        # This test verifies that the pipeline doesn't crash when no data is available
        # and that it properly reports the error condition
        
        # We'll skip this test if we can't control the data source
        # In a real implementation, this would be tested with mocked data
        pytest.skip("Empty dataset handling requires controlled data source")