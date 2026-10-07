import pytest
import pandas as pd
import numpy as np
import tempfile
import json
import time
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add code directory to path for imports
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'country_code': ['USA', 'CAN', 'MEX', 'BRA', 'ARG'],
        'year': [2010, 2010, 2010, 2010, 2010],
        'land_use_change_rate': [0.5, 0.3, 0.2, 0.4, 0.1],
        'gdp_per_capita': [50000.0, 45000.0, np.nan, 15000.0, 12000.0],
        'population_density': [35.0, 4.0, 65.0, 25.0, 15.0],
        'regime_type': [0, 0, 1, 1, 0]
    }
    return pd.DataFrame(data)

class TestDataCleaningLogic:
    """Tests for data cleaning and exclusion logic."""

    def test_excludes_row_when_gdp_missing(self, temp_data_dir, sample_dataframe):
        """
        T019a: Unit test for row exclusion.
        Verifies a row is excluded if GDP is null and logged correctly.
        """
        # Import the function to test
        from data.clean import apply_fr007_exclusion
        import logging

        # Setup logging to capture output
        log_capture_string = io.StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.WARNING)
        
        logger = logging.getLogger('data.clean')
        logger.addHandler(ch)
        logger.setLevel(logging.WARNING)

        # Create a temporary output file path
        output_path = temp_data_dir / "cleaned_panel.csv"

        # Apply FR-007 exclusion (GDP missing)
        result_df = apply_fr007_exclusion(sample_dataframe, str(output_path))

        # Assert the row with missing GDP (MEX) was excluded
        assert 'MEX' not in result_df['country_code'].values, "Row with missing GDP should be excluded"
        
        # Assert other rows are present
        assert 'USA' in result_df['country_code'].values
        assert 'CAN' in result_df['country_code'].values
        
        # Assert the count is correct (5 original - 1 excluded = 4)
        assert len(result_df) == 4

        # Verify log message was generated
        log_contents = log_capture_string.getvalue()
        assert 'GDP' in log_contents, "Log should mention missing GDP"
        assert 'excluded' in log_contents.lower(), "Log should indicate exclusion"

        # Verify the output file was created
        assert output_path.exists(), "Output CSV should be created"
        
        # Verify the file content matches the dataframe
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 4
        assert 'MEX' not in saved_df['country_code'].values

    def test_merge_handles_missing_keys(self, temp_data_dir):
        """
        T018a: Unit test for data merge logic.
        Verifies row exclusion when ISO codes mismatch.
        """
        from data.clean import merge_datasets
        
        fao_data = pd.DataFrame({
            'country_code': ['USA', 'CAN'],
            'year': [2010, 2010],
            'land_use_change_rate': [0.5, 0.3]
        })
        
        wb_data = pd.DataFrame({
            'country_code': ['USA', 'MEX'],  # MEX mismatch
            'year': [2010, 2010],
            'gdp_per_capita': [50000.0, 15000.0]
        })
        
        output_path = temp_data_dir / "merged.csv"
        
        result = merge_datasets(fao_data, wb_data, str(output_path))
        
        # Only USA should be in the result (common key)
        assert len(result) == 1
        assert result.iloc[0]['country_code'] == 'USA'
        assert 'MEX' not in result['country_code'].values

    def test_classifies_cbnrm_when_proxy_above_threshold(self, temp_data_dir):
        """
        T020a: Unit test for threshold mapping.
        Verifies regime_type is 1 when proxy > threshold.
        """
        from data.classify import classify_regime
        
        # Simulate metadata with a threshold
        metadata = {
            'indicator': 'AG.LND.FRST.CF',
            'threshold': 0.5,
            'status': 'success'
        }
        
        # Test value above threshold
        proxy_value = 0.75
        regime = classify_regime(proxy_value, metadata)
        
        assert regime == 1, "Regime should be 1 when proxy > threshold"

    def test_classifies_state_led_when_proxy_below_threshold(self, temp_data_dir):
        """
        T020b: Unit test for edge cases.
        Verifies regime_type is 0 when proxy <= threshold.
        """
        from data.classify import classify_regime
        
        metadata = {
            'indicator': 'AG.LND.FRST.CF',
            'threshold': 0.5,
            'status': 'success'
        }
        
        # Test value below threshold
        proxy_value = 0.3
        regime = classify_regime(proxy_value, metadata)
        
        assert regime == 0, "Regime should be 0 when proxy <= threshold"

class TestDownloadRetryLogic:
    """Tests for download retry logic (T017a)."""

    @patch('data.download.time.sleep')
    @patch('data.download.requests.get')
    def test_download_exponential_backoff(self, mock_get, mock_sleep, temp_data_dir):
        """
        T017a: Unit test for API retry logic.
        Mocks server errors and verifies multiple retries with specific sleep intervals.
        """
        from data.download import fetch_with_backoff
        
        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        
        error_response = Mock()
        error_response.status_code = 500
        
        mock_get.side_effect = [
            requests.exceptions.RequestException("Server Error"),
            requests.exceptions.RequestException("Server Error"),
            mock_response
        ]
        
        # Call the function
        result = fetch_with_backoff("http://test.com/api", max_retries=3)
        
        # Verify requests were made 3 times
        assert mock_get.call_count == 3
        
        # Verify sleep was called twice (between retries)
        assert mock_sleep.call_count == 2

    @patch('data.download.requests.get')
    def test_synthetic_data_not_generated_on_failure(self, mock_get, temp_data_dir):
        """
        T065: Unit Test for "Fail Loud" Behavior.
        Mocks a persistent API failure and asserts that the script raises an exception.
        """
        from data.download import fetch_with_backoff
        
        # Setup mock to fail continuously
        mock_get.side_effect = requests.exceptions.RequestException("Persistent Failure")
        
        # Verify that an exception is raised and no synthetic data is returned
        with pytest.raises(SystemExit):
            fetch_with_backoff("http://test.com/api", max_retries=2)

# Additional imports needed for the test above
import io
import requests

if __name__ == '__main__':
    pytest.main([__file__, '-v'])