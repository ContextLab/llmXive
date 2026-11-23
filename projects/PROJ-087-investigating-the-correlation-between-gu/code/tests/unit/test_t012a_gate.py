import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.ingestion import write_ingestion_report, fetch_sample_headers, verify_schema
from src.main import step_check_data

def test_write_ingestion_report_creates_file():
    """Test that write_ingestion_report creates the expected JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "ingestion_report.json")
        # Mock the output directory
        with patch('src.ingestion.Path') as mock_path:
            mock_path.return_value.mkdir.return_value = None
            mock_path.return_value.__truediv__.return_value = Path(output_path)
            
            write_ingestion_report(
                status="success",
                reason="Test",
                measurement_status="measurable",
                data_source="http://test.com"
            )
            
            # Check file exists and has correct content
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['status'] == 'success'
            assert data['reason'] == 'Test'
            assert data['measurement_status'] == 'measurable'
            assert data['data_source'] == 'http://test.com'

def test_verify_schema_success():
    """Test schema verification with all required columns."""
    headers = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours', 'other_col']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    assert verify_schema(headers, required) is True

def test_verify_schema_failure():
    """Test schema verification with missing columns."""
    headers = ['antibiotic_use_last_3m', 'other_col']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    assert verify_schema(headers, required) is False

@patch('src.main.plan_path')
@patch('src.main.write_ingestion_report')
@patch('src.main.fetch_sample_headers')
def test_step_check_data_success(mock_fetch, mock_write, mock_plan):
    """Test step_check_data when data source is valid."""
    mock_plan.exists.return_value = True
    mock_plan.read_text.return_value = "# Verified datasets\nhttps://example.com/data.csv"
    mock_fetch.return_value = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    
    args = MagicMock()
    result = step_check_data(args)
    
    assert result == 0
    mock_write.assert_called_once()
    call_args = mock_write.call_args[1]
    assert call_args['status'] == 'success'

@patch('src.main.plan_path')
@patch('src.main.write_ingestion_report')
def test_step_check_data_no_url(mock_write, mock_plan):
    """Test step_check_data when no URL is found in plan.md."""
    mock_plan.exists.return_value = True
    mock_plan.read_text.return_value = "# No verified datasets found"
    
    args = MagicMock()
    result = step_check_data(args)
    
    assert result == 1
    mock_write.assert_called_once()
    call_args = mock_write.call_args[1]
    assert call_args['status'] == 'blocked'
    assert "No verified data source" in call_args['reason']

@patch('src.main.plan_path')
@patch('src.main.write_ingestion_report')
def test_step_check_data_schema_failure(mock_write, mock_plan):
    """Test step_check_data when schema verification fails."""
    mock_plan.exists.return_value = True
    mock_plan.read_text.return_value = "# Verified datasets\nhttps://example.com/data.csv"
    
    with patch('src.main.fetch_sample_headers') as mock_fetch:
        mock_fetch.return_value = ['antibiotic_use_last_3m', 'other_col']
        
        args = MagicMock()
        result = step_check_data(args)
        
        assert result == 1
        mock_write.assert_called_once()
        call_args = mock_write.call_args[1]
        assert call_args['status'] == 'blocked'
        assert "Missing required columns" in call_args['reason']