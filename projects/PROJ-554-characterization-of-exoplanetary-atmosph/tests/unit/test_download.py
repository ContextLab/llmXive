import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from download import validate_sample_size

class TestValidateSampleSize:
    def test_sample_size_within_range(self, tmp_path):
        """Test when sample size is within the acceptable range."""
        mock_data = [
            {'planet_name': f'Planet_{i}', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'}
            for i in range(35)
        ]
        
        report_path = tmp_path / "sample_size_report.json"
        
        result = validate_sample_size(
            data=mock_data,
            min_threshold=30,
            max_threshold=45,
            output_path=str(report_path)
        )
        
        assert result['count'] == 35
        assert result['validation_status'] == 'proceed'
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            saved_report = json.load(f)
            assert saved_report['count'] == 35
            assert saved_report['validation_status'] == 'proceed'

    def test_sample_size_below_threshold(self, tmp_path, caplog):
        """Test when sample size is below the minimum threshold."""
        mock_data = [
            {'planet_name': f'Planet_{i}', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'}
            for i in range(20)
        ]
        
        report_path = tmp_path / "sample_size_report.json"
        
        # Capture log output
        with caplog.at_level("WARNING"):
            result = validate_sample_size(
                data=mock_data,
                min_threshold=30,
                max_threshold=45,
                output_path=str(report_path)
            )
        
        assert result['count'] == 20
        assert result['validation_status'] == 'proceed'
        assert "below" in result['message'].lower()
        
        # Verify log was written
        assert any("below" in record.message.lower() for record in caplog.records)

    def test_sample_size_above_threshold(self, tmp_path, caplog):
        """Test when sample size exceeds the maximum threshold."""
        mock_data = [
            {'planet_name': f'Planet_{i}', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'}
            for i in range(50)
        ]
        
        report_path = tmp_path / "sample_size_report.json"
        
        with caplog.at_level("WARNING"):
            result = validate_sample_size(
                data=mock_data,
                min_threshold=30,
                max_threshold=45,
                output_path=str(report_path)
            )
        
        assert result['count'] == 50
        assert result['validation_status'] == 'proceed'
        assert "exceeds" in result['message'].lower()
        
        assert any("exceeds" in record.message.lower() for record in caplog.records)

    def test_unique_planet_counting(self, tmp_path):
        """Test that unique planets are counted correctly even with duplicates."""
        mock_data = [
            {'planet_name': 'Planet_A', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'},
            {'planet_name': 'Planet_A', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'}, # Duplicate
            {'planet_name': 'Planet_B', 'temperature': 1000, 'metallicity': 0.1, 
             'snr': 10, 'resolution': 100, 'planet_category': 'Other', 
             'instrument': 'Test', 'wavelength_range': '1-2um'}
        ]
        
        report_path = tmp_path / "sample_size_report.json"
        
        result = validate_sample_size(
            data=mock_data,
            min_threshold=1,
            max_threshold=10,
            output_path=str(report_path)
        )
        
        # Should count 2 unique planets
        assert result['count'] == 2