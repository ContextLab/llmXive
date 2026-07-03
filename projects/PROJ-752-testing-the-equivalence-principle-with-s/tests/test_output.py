"""
Tests for the output generation and checksum verification logic in code/data/output.py
"""
import os
import json
import tempfile
import pandas as pd
import pytest

from data.output import compute_sha256, save_cleaned_data, record_checksum


def test_compute_sha256():
    """Test that SHA-256 checksum is computed correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = tmp.name
    
    try:
        checksum = compute_sha256(tmp_path)
        # Known SHA-256 hash for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    finally:
        os.unlink(tmp_path)


def test_save_cleaned_data():
    """Test saving cleaned data to CSV and computing checksum."""
    df = pd.DataFrame({
        "time": ["2023-01-01", "2023-01-02"],
        "range": [100.0, 200.0],
        "residual": [0.1, 0.2]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.csv")
        checksum_info = save_cleaned_data(df, output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify checksum info
        assert checksum_info["file"] == "test.csv"
        assert len(checksum_info["sha256"]) == 64  # SHA-256 hex length
        
        # Verify checksum is correct by recomputing
        recomputed = compute_sha256(output_path)
        assert checksum_info["sha256"] == recomputed


def test_record_checksum():
    """Test recording checksums to JSON file."""
    checksum_info = {
        "file": "test.csv",
        "sha256": "abc123"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = os.path.join(tmpdir, ".checksums.json")
        
        # First record
        record_checksum(checksum_info, checksum_file)
        
        with open(checksum_file, 'r') as f:
            data = json.load(f)
        
        assert "entries" in data
        assert len(data["entries"]) == 1
        assert data["entries"][0]["file"] == "test.csv"
        assert data["entries"][0]["sha256"] == "abc123"
        
        # Record another checksum
        checksum_info_2 = {
            "file": "test2.csv",
            "sha256": "def456"
        }
        record_checksum(checksum_info_2, checksum_file)
        
        with open(checksum_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["entries"]) == 2
        assert any(e["file"] == "test.csv" for e in data["entries"])
        assert any(e["file"] == "test2.csv" for e in data["entries"])
        
        # Update existing checksum
        checksum_info_updated = {
            "file": "test.csv",
            "sha256": "updated123"
        }
        record_checksum(checksum_info_updated, checksum_file)
        
        with open(checksum_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["entries"]) == 2
        test_entry = next(e for e in data["entries"] if e["file"] == "test.csv")
        assert test_entry["sha256"] == "updated123"


def test_save_and_record_integration():
    """Integration test: save data and record checksum in one flow."""
    df = pd.DataFrame({
        "time": ["2023-01-01"],
        "range": [100.0],
        "residual": [0.1]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cleaned_slr_data.csv")
        json_path = os.path.join(tmpdir, ".checksums.json")
        
        # Save data
        checksum_info = save_cleaned_data(df, csv_path)
        
        # Record checksum
        record_checksum(checksum_info, json_path)
        
        # Verify both files exist and are correct
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert data["entries"][0]["file"] == "cleaned_slr_data.csv"
        assert data["entries"][0]["sha256"] == checksum_info["sha256"]