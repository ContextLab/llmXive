import pytest
import os
import sys
import csv
import io
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import (
    fetch_kp_indices,
    validate_kp_schema,
    write_kp_data,
    KP_DATA_PATH
)

class TestFetchKpIndices:
    """Tests for Kp index fetching functionality."""
    
    @patch('ingest.requests.get')
    def test_fetch_kp_indices_success(self, mock_get):
        """Test successful fetch of Kp indices."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = """Time,Kp,Ap
        2023-01-01 00:00,2.3,15
        2023-01-01 03:00,3.0,20
        2023-01-01 06:00,2.7,18"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call function
        data = fetch_kp_indices()
        
        # Assertions
        assert len(data) == 3
        assert data[0]['time'] == '2023-01-01 00:00'
        assert data[0]['kp'] == '2.3'
        assert data[0]['ap'] == '15'
        
        mock_get.assert_called_once()
    
    @patch('ingest.requests.get')
    def test_fetch_kp_indices_empty_response(self, mock_get):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.text = "Time,Kp,Ap"  # Only header
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="No valid data found"):
            fetch_kp_indices()
    
    @patch('ingest.requests.get')
    def test_fetch_kp_indices_network_error(self, mock_get):
        """Test handling of network error."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch Kp indices"):
            fetch_kp_indices()

class TestValidateKpSchema:
    """Tests for Kp schema validation."""
    
    def test_valid_data(self):
        """Test validation with valid data."""
        data = [
            {'time': '2023-01-01 00:00', 'kp': '2.3', 'ap': '15'},
            {'time': '2023-01-01 03:00', 'kp': 'x', 'ap': '100'}
        ]
        
        is_valid, errors = validate_kp_schema(data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_field(self):
        """Test validation with missing field."""
        data = [
            {'time': '2023-01-01 00:00', 'kp': '2.3'}  # Missing 'ap'
        ]
        
        is_valid, errors = validate_kp_schema(data)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Missing required field 'ap'" in errors[0]
    
    def test_invalid_kp_value(self):
        """Test validation with invalid Kp value."""
        data = [
            {'time': '2023-01-01 00:00', 'kp': 'invalid', 'ap': '15'}
        ]
        
        is_valid, errors = validate_kp_schema(data)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid Kp value 'invalid'" in errors[0]
    
    def test_empty_data(self):
        """Test validation with empty data."""
        is_valid, errors = validate_kp_schema([])
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Data list is empty" in errors[0]

class TestWriteKpData:
    """Tests for Kp data writing."""
    
    def test_write_kp_data(self, tmp_path):
        """Test writing Kp data to CSV."""
        data = [
            {'time': '2023-01-01 00:00', 'kp': '2.3', 'ap': '15'},
            {'time': '2023-01-01 03:00', 'kp': '3.0', 'ap': '20'}
        ]
        
        output_path = tmp_path / "kp_test.csv"
        write_kp_data(data, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]['time'] == '2023-01-01 00:00'
        assert rows[0]['kp'] == '2.3'

class TestIntegration:
    """Integration tests for Kp ingestion pipeline."""
    
    @patch('ingest.requests.get')
    def test_full_kp_ingestion_flow(self, mock_get, tmp_path):
        """Test the full flow: fetch -> validate -> write."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = """Time,Kp,Ap
        2023-01-01 00:00,2.3,15
        2023-01-01 03:00,3.0,20"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        output_path = tmp_path / "kp_integration.csv"
        
        # Fetch
        data = fetch_kp_indices()
        
        # Validate
        is_valid, errors = validate_kp_schema(data)
        assert is_valid is True
        
        # Write
        write_kp_data(data, str(output_path))
        
        # Verify file
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['kp'] == '2.3'
        assert rows[1]['kp'] == '3.0'