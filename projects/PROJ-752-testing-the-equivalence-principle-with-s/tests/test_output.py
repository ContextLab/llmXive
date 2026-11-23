import os
import json
import tempfile
import pandas as pd
import pytest
from code.data.output import compute_sha256, save_cleaned_data, record_checksum, ensure_raw_data_preserved, run_output_pipeline

def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # Known hash for "test content"
        expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_save_cleaned_data():
    """Test saving a DataFrame to CSV."""
    df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test.csv')
        save_cleaned_data(df, output_path)
        
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path)
        assert loaded_df.equals(df)

def test_record_checksum():
    """Test recording checksum to JSON."""
    df = pd.DataFrame({'x': [1]})
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, 'data.csv')
        json_path = os.path.join(tmpdir, 'checksums.json')
        
        save_cleaned_data(df, csv_path)
        record_checksum(csv_path, json_path)
        
        assert os.path.exists(json_path)
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert 'data.csv' in data
        assert len(data['data.csv']) == 64  # SHA256 hex length

def test_ensure_raw_data_preserved():
    """Test raw data preservation check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy file in raw dir
        with open(os.path.join(tmpdir, 'raw.txt'), 'w') as f:
            f.write("raw")
        
        ensure_raw_data_preserved(tmpdir)  # Should not raise
        
        # Test empty dir
        empty_dir = os.path.join(tmpdir, 'empty')
        os.makedirs(empty_dir)
        with pytest.raises(ValueError):
            ensure_raw_data_preserved(empty_dir)

def test_run_output_pipeline():
    """Test the full output pipeline integration."""
    df = pd.DataFrame({'sat': ['LAGEOS'], 'res': [0.01]})
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = os.path.join(tmpdir, 'raw')
        os.makedirs(raw_dir)
        with open(os.path.join(raw_dir, 'source.raw'), 'w') as f:
            f.write("raw data")
        
        csv_out = os.path.join(tmpdir, 'cleaned.csv')
        json_out = os.path.join(tmpdir, '.checksums.json')
        
        run_output_pipeline(df, raw_dir, csv_out, json_out)
        
        assert os.path.exists(csv_out)
        assert os.path.exists(json_out)
        
        with open(json_out, 'r') as f:
            checksums = json.load(f)
        assert 'cleaned.csv' in checksums
