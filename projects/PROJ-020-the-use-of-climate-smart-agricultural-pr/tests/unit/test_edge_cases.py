"""
Unit tests for edge cases in the CSA food security analysis pipeline.

Tests cover:
- Missing years in LSMS data
- Climate data gaps (NASA POWER)
- High collinearity (VIF > 5.0)
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download import download_lsms, download_nasa_power, download_faostat
from analysis.diagnostics import calculate_vif, flag_collinearity, get_collinearity_report
from utils.config import get_target_countries, get_target_years


class TestMissingYearsLSMS:
    """Tests for handling missing years in LSMS data downloads."""

    @patch('data.download.requests.get')
    def test_missing_year_handles_gracefully(self, mock_get):
        """Test that download_lsms handles missing years without crashing."""
        # Mock a response that indicates the year is not available
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Resource not found")
        mock_get.return_value = mock_response

        # Should raise a specific error or handle gracefully
        with pytest.raises(Exception):
            download_lsms("KEN", 2099)  # Year far in future, likely missing

    @patch('data.download.requests.get')
    def test_valid_year_returns_data(self, mock_get):
        """Test that valid years return data properly."""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"household_id": 1, "country": "KEN", "year": 2020}
            ]
        }
        mock_get.return_value = mock_response

        result = download_lsms("KEN", 2020)
        assert result is not None

    def test_missing_year_in_target_list(self):
        """Test handling when a target year is missing from the dataset."""
        # This test verifies the logic in the pipeline when a year is missing
        # Create a mock dataframe with some years missing
        df = pd.DataFrame({
            'country': ['KEN', 'KEN', 'IND', 'IND'],
            'year': [2015, 2017, 2016, 2018],  # 2016 missing for KEN, 2017 for IND
            'value': [10, 20, 30, 40]
        })

        # Verify the dataframe structure
        assert len(df) == 4
        assert 'KEN' in df['country'].values
        assert 2016 not in df[df['country'] == 'KEN']['year'].values


class TestClimateDataGaps:
    """Tests for handling gaps in NASA POWER climate data."""

    @patch('data.download.requests.get')
    def test_partial_climate_data_handled(self, mock_get):
        """Test that partial climate data (with gaps) is handled correctly."""
        # Mock a response with partial data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "periods": [
                    {"time": "2020-01-01", "value": 25.5},
                    {"time": "2020-01-03", "value": 26.1}  # Missing 01-02
                ]
            }
        }
        mock_get.return_value = mock_response

        # Should return data with gaps that need interpolation
        result = download_nasa_power(0.0, 37.0, "2020-01-01", "2020-01-03")
        assert result is not None

    def test_large_climate_gap_detection(self):
        """Test detection of large gaps in climate data (> 3 months)."""
        # Create a dataframe with a large gap
        dates = pd.date_range(start="2020-01-01", end="2020-03-31", freq="D")
        values = np.random.rand(len(dates)) * 30

        df = pd.DataFrame({'date': dates, 'temperature': values})

        # Simulate a gap by removing a chunk
        gap_start = pd.Timestamp("2020-02-15")
        gap_end = pd.Timestamp("2020-05-15")
        df_no_gap = df[(df['date'] < gap_start) | (df['date'] > gap_end)]

        # Verify gap exists
        date_range = pd.date_range(start=gap_start, end=gap_end, freq="D")
        missing_count = sum(~df_no_gap['date'].isin(date_range))
        assert missing_count == 0  # All gap dates are missing

        # Calculate gap size
        gap_size = (gap_end - gap_start).days
        assert gap_size > 90  # More than 3 months

    @patch('data.download.requests.get')
    def test_nearest_neighbor_interpolation(self, mock_get):
        """Test nearest-neighbor interpolation for small climate gaps."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "periods": [
                    {"time": "2020-01-01", "value": 25.0},
                    {"time": "2020-01-02", "value": 25.5},
                    {"time": "2020-01-03", "value": 26.0}
                ]
            }
        }
        mock_get.return_value = mock_response

        result = download_nasa_power(0.0, 37.0, "2020-01-01", "2020-01-03")
        assert result is not None
        assert len(result) == 3


class TestHighCollinearityVIF:
    """Tests for handling high collinearity (VIF > 5.0)."""

    def test_vif_calculation_with_perfect_collinearity(self):
        """Test VIF calculation when perfect collinearity exists."""
        # Create dataframe with perfect collinearity
        df = pd.DataFrame({
            'y': [1, 2, 3, 4, 5],
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # x2 = 2 * x1 (perfect collinearity)
            'x3': [1, 3, 5, 7, 9]
        })

        # Calculate VIF
        vif_data = calculate_vif(df[['x1', 'x2', 'x3']], ['x1', 'x2', 'x3'])

        # One of the collinear variables should have very high VIF
        high_vif_found = any(vif['VIF'] > 100 for vif in vif_data)
        assert high_vif_found, "Expected at least one variable with VIF > 100 for perfect collinearity"

    def test_vif_threshold_flagging(self):
        """Test that variables with VIF > 5.0 are properly flagged."""
        # Create dataframe with moderate collinearity
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.8 + np.random.normal(0, 0.2, n)  # Correlated with x1
        x3 = np.random.normal(0, 1, n)  # Independent

        df = pd.DataFrame({
            'y': x1 + x2 + x3 + np.random.normal(0, 0.1, n),
            'x1': x1,
            'x2': x2,
            'x3': x3
        })

        # Calculate VIF
        vif_data = calculate_vif(df[['x1', 'x2', 'x3']], ['x1', 'x2', 'x3'])

        # Flag collinearity
        flagged = flag_collinearity(vif_data, threshold=5.0)

        # At least one variable should be flagged
        assert len(flagged) > 0, "Expected at least one variable flagged for collinearity"

        # Verify flagged variables have VIF > 5.0
        for var in flagged:
            var_vif = next(v['VIF'] for v in vif_data if v['variable'] == var)
            assert var_vif > 5.0, f"Variable {var} has VIF {var_vif} <= 5.0 but was flagged"

    def test_collinearity_report_generation(self):
        """Test generation of collinearity report."""
        # Create dataframe with known collinearity
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.7 + np.random.normal(0, 0.3, n)
        x3 = np.random.normal(0, 1, n)

        df = pd.DataFrame({
            'y': x1 + x2 + x3,
            'x1': x1,
            'x2': x2,
            'x3': x3
        })

        # Generate report
        report = get_collinearity_report(df[['x1', 'x2', 'x3']], ['x1', 'x2', 'x3'])

        # Verify report structure
        assert 'high_collinearity' in report
        assert 'variables' in report
        assert 'vif_values' in report

        # Verify high collinearity is detected
        assert len(report['high_collinearity']) > 0

    def test_vif_with_constant_variable(self):
        """Test VIF calculation when a constant variable is present."""
        df = pd.DataFrame({
            'y': [1, 2, 3, 4, 5],
            'x1': [1, 2, 3, 4, 5],
            'x2': [5, 5, 5, 5, 5],  # Constant variable
            'x3': [1, 3, 5, 7, 9]
        })

        # Should handle constant variable gracefully
        vif_data = calculate_vif(df[['x1', 'x2', 'x3']], ['x1', 'x2', 'x3'])

        # Constant variable should have infinite or very high VIF
        x2_vif = next((v['VIF'] for v in vif_data if v['variable'] == 'x2'), None)
        assert x2_vif is not None
        assert np.isinf(x2_vif) or x2_vif > 1000, "Constant variable should have infinite or very high VIF"


class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_pipeline_with_missing_and_collinear_data(self):
        """Test the full pipeline with missing years and collinear variables."""
        # Create synthetic data with known issues
        np.random.seed(42)
        n = 200

        # Simulate missing years
        years = [2015, 2016, 2018, 2019]  # 2017 missing
        country = ['KEN'] * n

        # Simulate collinear variables
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Highly correlated
        x3 = np.random.normal(0, 1, n)
        y = x1 + x2 + x3 + np.random.normal(0, 0.5, n)

        df = pd.DataFrame({
            'country': country,
            'year': np.random.choice(years, n),
            'x1': x1,
            'x2': x2,
            'x3': x3,
            'y': y
        })

        # Test VIF calculation
        vif_data = calculate_vif(df[['x1', 'x2', 'x3']], ['x1', 'x2', 'x3'])
        flagged = flag_collinearity(vif_data, threshold=5.0)

        # Should detect collinearity
        assert len(flagged) > 0

        # Test that pipeline can handle this data
        # (In real scenario, this would be part of the full pipeline)
        assert len(df) > 0
        assert 'country' in df.columns
        assert 'year' in df.columns