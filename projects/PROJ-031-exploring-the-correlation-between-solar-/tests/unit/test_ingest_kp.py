"""
Unit tests for Kp index ingestion functionality.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingest import fetch_kp_indices_http, write_kp_data, validate_kp_schema, DataFetchError

class TestKpIngestion:
    """Tests for Kp index ingestion."""

    def test_validate_kp_schema_valid(self):
        """Test validation passes for valid schema."""
        df = pd.DataFrame({
            'time': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 03:00:00']),
            'kp': [2.0, 3.0]
        })
        # Should not raise
        validate_kp_schema(df)

    def test_validate_kp_schema_missing_column(self):
        """Test validation fails for missing column."""
        df = pd.DataFrame({
            'time': pd.to_datetime(['2023-01-01 00:00:00']),
            'value': [2.0]
        })
        with pytest.raises(ValueError, match="missing required columns"):
            validate_kp_schema(df)

    def test_validate_kp_schema_empty(self):
        """Test validation fails for empty dataframe."""
        df = pd.DataFrame({'time': pd.to_datetime([]), 'kp': []})
        with pytest.raises(ValueError, match="Kp data is empty"):
            validate_kp_schema(df)

    @patch('ingest.requests.get')
    def test_fetch_kp_indices_http_success(self, mock_get):
        """Test successful fetch of Kp indices."""
        # Mock HTML response
        mock_html = """
        <html>
        <body>
        <table>
            <tr><th>Date</th><th>00Z</th><th>03Z</th><th>06Z</th><th>09Z</th><th>12Z</th><th>15Z</th><th>18Z</th><th>21Z</th></tr>
            <tr><td>2023-01-01</td><td>2</td><td>2+</td><td>3</td><td>3-</td><td>3+</td><td>4</td><td>4-</td><td>4+</td></tr>
            <tr><td>2023-01-02</td><td>5</td><td>5+</td><td>6</td><td>6-</td><td>6+</td><td>7</td><td>7-</td><td>7+</td></tr>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = fetch_kp_indices_http()
        
        assert not df.empty
        assert 'time' in df.columns
        assert 'kp' in df.columns
        assert len(df) == 16  # 2 days * 8 hours
        assert pd.api.types.is_datetime64_any_dtype(df['time'])

    @patch('ingest.requests.get')
    def test_fetch_kp_indices_http_no_table(self, mock_get):
        """Test fetch fails when no table found."""
        mock_html = "<html><body>No table here</body></html>"
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(DataFetchError, match="No tables found"):
            fetch_kp_indices_http()

    @patch('ingest.requests.get')
    def test_fetch_kp_indices_http_no_rows(self, mock_get):
        """Test fetch fails when no data rows found."""
        mock_html = """
        <html>
        <body>
        <table>
            <tr><th>Date</th><th>00Z</th></tr>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(DataFetchError, match="No Kp data rows"):
            fetch_kp_indices_http()

    def test_write_kp_data(self, tmp_path):
        """Test writing Kp data to CSV."""
        df = pd.DataFrame({
            'time': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 03:00:00']),
            'kp': [2.0, 3.0]
        })
        output_path = str(tmp_path / "kp_test.csv")
        write_kp_data(df, output_path)
        
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert 'time' in loaded_df.columns
        assert 'kp' in loaded_df.columns