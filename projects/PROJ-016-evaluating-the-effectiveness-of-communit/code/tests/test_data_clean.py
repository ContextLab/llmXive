import pytest
import pandas as pd
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import sys
import time

# Import the function we are testing from the clean module.
# Based on the API surface, the classification logic is in `classify.py`,
# but T020b asks for a test in `test_data_clean.py`. We will test the
# application of the classification logic as it would be used by clean.py
# or directly test the logic if it were imported there.
# However, looking at the API surface for `code/data/clean.py`, it exports
# `apply_classification`? No, it exports `apply_fr007_exclusion`, etc.
# The API surface for `code/data/classify.py` exports `apply_classification`.
# Since the task specifically asks to add the test to `test_data_clean.py`,
# we will import `apply_classification` from `data.classify` (as allowed by
# the project structure) and test it here, or we assume `clean.py` wraps it.
# To be safe and strictly follow "extend test_data_clean.py", we import the
# logic from the correct module (classify) but place the test case here.
from data.classify import apply_classification
from data.download import fetch_with_backoff

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'country_code': ['USA', 'CAN', 'MEX'],
        'year': [2000, 2000, 2000],
        'land_use_change': [0.5, 0.2, 0.3],
        'cbnrm_proxy': [0.8, 0.2, 0.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestDataCleaningLogic:
    """Tests for data cleaning and classification logic."""

    def test_classifies_state_led_when_proxy_below_threshold(self, sample_dataframe, temp_data_dir):
        """
        Test that regime_type is 0 when proxy <= threshold.
        
        This test verifies the edge case where the proxy value is exactly
        at or below the threshold, resulting in a 'State-Led' classification (0).
        """
        # Setup: Create a metadata file with a threshold
        threshold = 0.5
        metadata_path = temp_data_dir / "cbnrm_proxy_metadata.json"
        
        metadata = {
            "indicator_code": "AG.LND.FRST.CF",
            "threshold": threshold,
            "source": "World Bank"
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Create a dataframe where one value is exactly at threshold, one below, one above
        df = sample_dataframe.copy()
        # Ensure the 'cbnrm_proxy' column exists and has specific values
        df.loc[0, 'cbnrm_proxy'] = 0.4  # Below threshold -> 0
        df.loc[1, 'cbnrm_proxy'] = 0.5  # Equal to threshold -> 0 (per task: proxy <= threshold)
        df.loc[2, 'cbnrm_proxy'] = 0.6  # Above threshold -> 1 (for contrast)
        
        # Execute: Call the classification function
        # We assume apply_classification takes df, metadata_path, and column name
        result_df = apply_classification(df, str(metadata_path), 'cbnrm_proxy')
        
        # Verify: Check that regime_type is correctly set
        assert 'regime_type' in result_df.columns
        
        # Row 0: 0.4 <= 0.5 -> 0
        assert result_df.loc[0, 'regime_type'] == 0
        # Row 1: 0.5 <= 0.5 -> 0 (Edge case)
        assert result_df.loc[1, 'regime_type'] == 0
        # Row 2: 0.6 > 0.5 -> 1
        assert result_df.loc[2, 'regime_type'] == 1

    def test_classifies_cbnrm_when_proxy_above_threshold(self, sample_dataframe, temp_data_dir):
        """
        Test that regime_type is 1 when proxy > threshold.
        (Complementary test to T020a, ensuring the positive case works).
        """
        threshold = 0.5
        metadata_path = temp_data_dir / "cbnrm_proxy_metadata.json"
        
        metadata = {
            "indicator_code": "AG.LND.FRST.CF",
            "threshold": threshold,
            "source": "World Bank"
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        df = sample_dataframe.copy()
        df.loc[0, 'cbnrm_proxy'] = 0.9  # Above -> 1
        
        result_df = apply_classification(df, str(metadata_path), 'cbnrm_proxy')
        
        assert result_df.loc[0, 'regime_type'] == 1

    def test_fetch_fails_loudly_no_synthetic(self, temp_data_dir):
        """
        Unit Test for "Fail Loud" Behavior (T065).
        
        This test mocks a persistent API failure (simulating 3 consecutive 500 errors)
        and asserts that the script `fetch_with_backoff` raises an exception
        and does NOT generate or return any synthetic/mock data.
        
        This ensures the "Fail Loud" protocol in T060 is strictly enforced.
        """
        # Setup: Mock the requests.get to always raise a 500 error
        # We need to simulate 3 failures to trigger the max retries logic
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        
        # Configure the mock to return the error response 3 times
        with patch('data.download.requests.get', return_value=mock_response) as mock_get:
            # We expect the function to retry 3 times.
            # The function should raise an exception after the retries are exhausted.
            
            # Prepare a dummy URL and indicator
            test_url = "http://fake-api.example.com/data"
            test_indicator = "FAKE.IND.001"
            
            # Act & Assert: Verify that an exception is raised
            # We expect a requests.exceptions.HTTPError or a generic Exception
            # depending on how fetch_with_backoff wraps the final failure.
            # Based on T060 description: "raise (let the run fail)"
            
            with pytest.raises(Exception):
                # Call the function with max_retries=3 (default or explicit)
                # The function should attempt 3 times and then raise.
                fetch_with_backoff(test_url, indicator=test_indicator, max_retries=3)
            
            # Verify that requests.get was called exactly 3 times (the retries)
            assert mock_get.call_count == 3
            
            # CRITICAL ASSERTION: Ensure NO synthetic data was generated or returned.
            # If the function had a fallback, it would have returned a DataFrame or similar.
            # Since we are asserting an exception, we verify no synthetic data path was taken.
            # The fact that an exception was raised confirms the "Fail Loud" behavior.
            # We also verify that no 'generate_synthetic' function was called in the module.
            with patch('data.download.generate_synthetic_data') as mock_gen:
                try:
                    fetch_with_backoff(test_url, indicator=test_indicator, max_retries=3)
                except Exception:
                    pass
                
                # Assert that the synthetic generator was NEVER called
                assert mock_gen.call_count == 0, "Synthetic data generator was called despite API failure!"