"""
Tests for the scarcity flag logic in ingest.py (T016b).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest import handle_scarcity, PROJECT_ROOT, DATA_PROCESSED_DIR

class TestScarcityFlag:
    """Test cases for scarcity flag generation."""

    def test_scarcity_flag_below_threshold(self):
        """Test that scarcity status is 'scarcity' when count is below threshold."""
        threshold = 120
        count = 50  # Below threshold
        
        result = handle_scarcity(count, threshold)
        
        assert result['count'] == count
        assert result['status'] == 'scarcity'
        assert result['threshold'] == threshold
        
        # Verify file was written
        flag_file = DATA_PROCESSED_DIR / 'data_scarcity_flag.json'
        assert flag_file.exists(), f"Scarcity flag file {flag_file} was not created."
        
        with open(flag_file, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == result

    def test_scarcity_flag_above_threshold(self):
        """Test that scarcity status is 'sufficient' when count is above threshold."""
        threshold = 120
        count = 200  # Above threshold
        
        result = handle_scarcity(count, threshold)
        
        assert result['count'] == count
        assert result['status'] == 'sufficient'
        assert result['threshold'] == threshold
        
        # Verify file was written
        flag_file = DATA_PROCESSED_DIR / 'data_scarcity_flag.json'
        assert flag_file.exists(), f"Scarcity flag file {flag_file} was not created."
        
        with open(flag_file, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == result

    def test_scarcity_flag_exact_threshold(self):
        """Test that scarcity status is 'sufficient' when count equals threshold."""
        threshold = 120
        count = 120  # Exactly at threshold
        
        result = handle_scarcity(count, threshold)
        
        assert result['count'] == count
        assert result['status'] == 'sufficient'  # >= threshold is sufficient
        assert result['threshold'] == threshold

    def test_scarcity_flag_default_threshold(self):
        """Test that default threshold from config is used if not provided."""
        # This test assumes the config module is correctly loaded
        # We mock the config to ensure we get a known value
        with patch('src.data.ingest.config') as mock_config:
            mock_config.get.return_value = 150
            count = 140  # Below mocked threshold
            
            result = handle_scarcity(count)  # No threshold provided
            
            assert result['threshold'] == 150
            assert result['status'] == 'scarcity'

    def test_scarcity_flag_output_schema(self):
        """Test that the output file adheres to the required schema."""
        count = 100
        threshold = 120
        
        handle_scarcity(count, threshold)
        
        flag_file = DATA_PROCESSED_DIR / 'data_scarcity_flag.json'
        with open(flag_file, 'r') as f:
            data = json.load(f)
        
        # Check required keys
        assert 'count' in data
        assert 'status' in data
        assert 'threshold' in data
        
        # Check types
        assert isinstance(data['count'], int)
        assert isinstance(data['status'], str)
        assert data['status'] in ['scarcity', 'sufficient']
        assert isinstance(data['threshold'], int)
        
        # Check values match input
        assert data['count'] == count
        assert data['threshold'] == threshold
        assert data['status'] == 'scarcity' if count < threshold else 'sufficient'