"""
Unit tests for ingestion module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from ingestion import validate_dataset_size, save_metadata, count_raw_records_from_csv, parse_cognitive_status

class TestValidateDatasetSize:
    def test_sufficient_sample_size(self):
        """Test with sufficient sample size (>= 500 per group)."""
        data = {
            'cognitive_status': ['Control'] * 500 + ['MCI'] * 500 + ['AD'] * 500
        }
        df = pd.DataFrame(data)
        
        result = validate_dataset_size(df)
        
        assert result['is_valid'] is True
        assert result['low_power'] is False
        assert len(result['warnings']) == 0

    def test_insufficient_sample_size(self):
        """Test with insufficient sample size (< 500 per group)."""
        data = {
            'cognitive_status': ['Control'] * 400 + ['MCI'] * 400 + ['AD'] * 400
        }
        df = pd.DataFrame(data)
        
        result = validate_dataset_size(df)
        
        assert result['is_valid'] is False
        assert result['low_power'] is True
        assert len(result['warnings']) == 3  # One warning per group

    def test_mixed_sample_size(self):
        """Test with mixed sample sizes."""
        data = {
            'cognitive_status': ['Control'] * 600 + ['MCI'] * 400 + ['AD'] * 500
        }
        df = pd.DataFrame(data)
        
        result = validate_dataset_size(df)
        
        assert result['is_valid'] is False
        assert result['low_power'] is True
        assert len(result['warnings']) == 1  # Only MCI group has < 500

class TestSaveMetadata:
    def test_save_metadata_creates_file(self):
        """Test that save_metadata creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_path to use temp directory
            with patch('ingestion.get_path', return_value=Path(tmpdir) / 'metadata.json'):
                metadata = {'test': 'value'}
                save_metadata(metadata)
                
                output_path = Path(tmpdir) / 'metadata.json'
                assert output_path.exists()
                
                with open(output_path, 'r') as f:
                    saved_metadata = json.load(f)
                
                assert saved_metadata == metadata

class TestCountRawRecordsFromCsv:
    def test_count_records(self):
        """Test counting records in a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test.csv'
            
            # Create a test CSV
            data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            count = count_raw_records_from_csv(csv_path)
            assert count == 3

class TestParseCognitiveStatus:
    def test_parse_control(self):
        """Test parsing Control status."""
        assert parse_cognitive_status("This is a control subject") == 'Control'
        assert parse_cognitive_status("Healthy individual") == 'Control'

    def test_parse_mci(self):
        """Test parsing MCI status."""
        assert parse_cognitive_status("Mild cognitive impairment") == 'MCI'
        assert parse_cognitive_status("MCI patient") == 'MCI'

    def test_parse_ad(self):
        """Test parsing AD status."""
        assert parse_cognitive_status("Alzheimer's disease") == 'AD'
        assert parse_cognitive_status("AD patient") == 'AD'

    def test_parse_unknown(self):
        """Test parsing unknown status."""
        assert parse_cognitive_status("Unknown condition") == 'Unknown'
        assert parse_cognitive_status("") == 'Unknown'