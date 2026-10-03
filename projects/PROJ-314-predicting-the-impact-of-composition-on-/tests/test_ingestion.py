"""
Unit tests for ingestion pipeline.
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion import validate_data_gap, generate_data_availability_report, validate_url_reachability

def test_validate_data_gap_insufficient():
    """Test data gap validation with insufficient data."""
    with patch('ingestion.generate_data_availability_report') as mock_report:
        with patch('sys.exit') as mock_exit:
            result = validate_data_gap(29)
            assert result is False
            mock_report.assert_called_once()
            mock_exit.assert_called_once_with(1)

def test_validate_data_gap_sufficient():
    """Test data gap validation with sufficient data."""
    result = validate_data_gap(50)
    assert result is True

def test_generate_data_availability_report():
    """Test data availability report generation."""
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_report.json')
        generate_data_availability_report(20, output_path)
        assert Path(output_path).exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        assert report['total_entries'] == 20
        assert report['status'] == 'insufficient'