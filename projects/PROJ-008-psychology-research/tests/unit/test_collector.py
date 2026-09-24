"""
Unit tests for the API Collector (T016).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.data.collector import APICollector, main

@pytest.fixture
def mock_data_file():
    """Create a temporary mock data file."""
    mock_content = [
        {
            "id": "NCT000001",
            "title": "Mock Study 1",
            "description": "A study on mindfulness and ASD.",
            "age_range": {"min": 8, "max": 12},
            "diagnosis": "ASD",
            "outcomes": ["SRS-2"],
            "intervention_components": ["breathing"],
            "delivery_format": "caregiver-mediated",
            "abstract": "This study tests..."
        },
        {
            "id": "NCT000002",
            "title": "Mock Study 2 (No Abstract)",
            "description": "Another study.",
            "age_range": {"min": 10, "max": 11},
            "diagnosis": "ASD",
            "outcomes": ["SSIS"],
            "intervention_components": ["body scan"],
            "delivery_format": "child-led",
            "abstract": None
        }
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_content, f)
        yield f.name
    os.unlink(f.name)

def test_collector_uses_mock_data(mock_data_file):
    """Test that collector loads mock data when file is present."""
    collector = APICollector(mock_data_path=mock_data_file)
    studies = collector.collect(2015, 2024)
    
    assert len(studies) == 2
    assert studies[0]["id"] == "NCT000001"
    assert studies[1]["id"] == "NCT000002"
    
    # Verify log was populated
    assert len(collector.retrieval_log) == 2
    assert all(entry["status_code"] == 200 for entry in collector.retrieval_log)

def test_collector_fails_without_requests_in_live_mode():
    """Test that collector raises error if requests is missing in live mode."""
    # Ensure no mock path is provided
    collector = APICollector(mock_data_path=None)
    
    with patch('code.data.collector.REQUESTS_AVAILABLE', False):
        with pytest.raises(RuntimeError, match="requests library is required"):
            collector.collect(2015, 2024)

def test_save_retrieval_log():
    """Test that retrieval log is saved correctly."""
    collector = APICollector()
    collector.retrieval_log = [
        {"query": "test", "timestamp": "2023-01-01", "status_code": 200, "source": "test"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "log.json")
        collector.save_retrieval_log(log_path)
        
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["status_code"] == 200

def test_main_with_mock():
    """Test main function with mock data argument."""
    mock_content = [{"id": "TEST1"}]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_content, f)
        mock_path = f.name
    
    log_path = os.path.join(tempfile.gettempdir(), "test_log.json")
    
    try:
        # Mock sys.argv
        import sys
        original_argv = sys.argv
        sys.argv = ["collector.py", "--mock-path", mock_path, "--output-log", log_path]
        
        result = main()
        
        assert result == 0
        assert os.path.exists(log_path)
    finally:
        sys.argv = original_argv
        os.unlink(mock_path)
        if os.path.exists(log_path):
            os.unlink(log_path)