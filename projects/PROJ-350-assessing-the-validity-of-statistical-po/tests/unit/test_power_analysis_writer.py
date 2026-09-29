"""
Unit tests for T026: power_analysis_writer.py

Tests the logic of writing the final analysis dataset to CSV.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.power_analysis_writer import process_and_write_analysis, load_study_records
from code.utils.data_hygiene import ensure_directory

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_raw_records(temp_dir):
    """Create sample raw study records for testing."""
    records = [
        {
            "study_id": "S001",
            "osf_id": "abc123",
            "field": "Psychology",
            "effect_size_domain": "Medium",
            "planned_power": 0.8,
            "target_n": 100,
            "effect_size_assumption": 0.3,
            "actual_sample_size": 95,
            "missing_planned_data": False,
            "missing_actual_data": False,
            "validation_flags": []
        },
        {
            "study_id": "S002",
            "osf_id": "def456",
            "field": "Neuroscience",
            "effect_size_domain": "Small",
            "planned_power": 0.9,
            "target_n": 150,
            "effect_size_assumption": 0.2,
            "actual_sample_size": 140,
            "missing_planned_data": False,
            "missing_actual_data": False,
            "validation_flags": []
        }
    ]
    
    raw_file = temp_dir / "study_records_raw.json"
    with open(raw_file, 'w') as f:
        json.dump(records, f)
    
    return raw_file

def test_load_study_records(sample_raw_records, temp_dir):
    """Test that load_study_records correctly reads the JSON file."""
    # Temporarily override the path for testing
    with patch('code.power_analysis_writer.RAW_RECORDS_PATH', sample_raw_records):
        records = load_study_records()
        
    assert len(records) == 2
    assert records[0]['study_id'] == 'S001'
    assert records[1]['osf_id'] == 'def456'

def test_process_and_write_analysis(sample_raw_records, temp_dir):
    """Test the full process_and_write_analysis workflow."""
    # Create a temporary output path
    output_csv = temp_dir / "power_analysis.csv"
    processed_json = temp_dir / "study_records_processed.json"
    
    # Mock the paths
    with patch('code.power_analysis_writer.RAW_RECORDS_PATH', sample_raw_records), \
         patch('code.power_analysis_writer.OUTPUT_CSV_PATH', output_csv), \
         patch('code.power_analysis_writer.PROCESSED_RECORDS_PATH', processed_json):
        
        # We need to mock the process_study_records function to avoid dependency on full pipeline
        # For this test, we'll simulate what it should return
        mock_processed = [
            {
                "study_id": "S001",
                "osf_id": "abc123",
                "field": "Psychology",
                "effect_size_domain": "Medium",
                "planned_power": 0.8,
                "target_n": 100,
                "effect_size_assumption": 0.3,
                "actual_sample_size": 95,
                "sensitivity_power": 0.75,  # Mocked
                "power_gap": 0.05,           # 0.8 - 0.75
                "missing_planned_data": False,
                "missing_actual_data": False,
                "validation_flags": []
            },
            {
                "study_id": "S002",
                "osf_id": "def456",
                "field": "Neuroscience",
                "effect_size_domain": "Small",
                "planned_power": 0.9,
                "target_n": 150,
                "effect_size_assumption": 0.2,
                "actual_sample_size": 140,
                "sensitivity_power": 0.85,   # Mocked
                "power_gap": 0.15,           # 0.9 - 0.85
                "missing_planned_data": False,
                "missing_actual_data": False,
                "validation_flags": []
            }
        ]
        
        with patch('code.power_analysis_writer.process_study_records', return_value=mock_processed):
            count = process_and_write_analysis()
    
    # Verify the output file was created
    assert output_csv.exists()
    assert processed_json.exists()
    
    # Verify the count
    assert count == 2
    
    # Verify CSV content
    with open(output_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert rows[0]['study_id'] == 'S001'
    assert rows[0]['power_gap'] == '0.05'  # CSV writes as string
    assert rows[1]['study_id'] == 'S002'
    assert rows[1]['power_gap'] == '0.15'

def test_empty_records_handling(temp_dir):
    """Test handling of empty raw records."""
    raw_file = temp_dir / "study_records_raw.json"
    with open(raw_file, 'w') as f:
        json.dump([], f)
    
    output_csv = temp_dir / "power_analysis.csv"
    
    with patch('code.power_analysis_writer.RAW_RECORDS_PATH', raw_file), \
         patch('code.power_analysis_writer.OUTPUT_CSV_PATH', output_csv):
        count = process_and_write_analysis()
    
    assert output_csv.exists()
    assert count == 0
    
    # Verify headers exist even with no data
    with open(output_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
    
    expected_headers = [
        'study_id', 'osf_id', 'field', 'effect_size_domain',
        'planned_power', 'target_n', 'effect_size_assumption',
        'actual_sample_size', 'sensitivity_power', 'power_gap',
        'missing_planned_data', 'missing_actual_data', 'validation_flags'
    ]
    assert headers == expected_headers

def test_missing_raw_file(temp_dir):
    """Test error handling when raw file is missing."""
    missing_file = temp_dir / "nonexistent.json"
    output_csv = temp_dir / "power_analysis.csv"
    
    with patch('code.power_analysis_writer.RAW_RECORDS_PATH', missing_file), \
         patch('code.power_analysis_writer.OUTPUT_CSV_PATH', output_csv):
        with pytest.raises(FileNotFoundError, match="Raw study records not found"):
            process_and_write_analysis()