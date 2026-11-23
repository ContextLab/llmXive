import os
import json
import pandas as pd
import pytest
import tempfile
import shutil
from pathlib import Path

# Ensure code is in path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.output import compute_sha256, save_cleaned_data, record_checksum, run_output_pipeline, ensure_raw_data_preserved
from utils.logging import AnalysisError

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    base = tempfile.mkdtemp()
    raw_dir = os.path.join(base, "raw")
    processed_dir = os.path.join(base, "processed")
    os.makedirs(raw_dir)
    os.makedirs(processed_dir)
    
    # Create a dummy raw file to simulate preservation
    with open(os.path.join(raw_dir, "dummy_raw.txt"), "w") as f:
        f.write("dummy")
        
    yield {
        "base": base,
        "raw": raw_dir,
        "processed": processed_dir
    }
    
    shutil.rmtree(base)

def test_compute_sha256(temp_dirs):
    """Test SHA256 computation on a known file."""
    test_file = os.path.join(temp_dirs["raw"], "test.txt")
    content = "Hello, World!"
    with open(test_file, "w") as f:
        f.write(content)
    
    checksum = compute_sha256(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    
    # Verify against known hash for "Hello, World!"
    import hashlib
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert checksum == expected

def test_save_cleaned_data(temp_dirs):
    """Test saving a DataFrame to CSV."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    output_path = os.path.join(temp_dirs["processed"], "test.csv")
    
    save_cleaned_data(df, output_path)
    
    assert os.path.exists(output_path)
    loaded_df = pd.read_csv(output_path)
    assert loaded_df.equals(df)

def test_record_checksum(temp_dirs):
    """Test recording checksum to JSON."""
    test_file = os.path.join(temp_dirs["raw"], "test.txt")
    with open(test_file, "w") as f:
        f.write("test")
    
    record_checksum(test_file, temp_dirs["raw"])
    
    checksum_file = os.path.join(temp_dirs["raw"], ".checksums.json")
    assert os.path.exists(checksum_file)
    
    with open(checksum_file, "r") as f:
        data = json.load(f)
    
    assert "test.txt" in data
    assert "sha256" in data["test.txt"]
    assert data["test.txt"]["file"] == "test.txt"

def test_ensure_raw_data_preserved(temp_dirs):
    """Test raw data preservation check."""
    # Should return True because dummy file exists
    assert ensure_raw_data_preserved(temp_dirs["raw"], temp_dirs["processed"]) is True
    
    # Test with empty directory
    empty_dir = os.path.join(temp_dirs["base"], "empty")
    os.makedirs(empty_dir)
    assert ensure_raw_data_preserved(empty_dir, temp_dirs["processed"]) is False
    
    # Test with non-existent directory
    assert ensure_raw_data_preserved(os.path.join(temp_dirs["base"], "missing"), temp_dirs["processed"]) is False

def test_run_output_pipeline(temp_dirs):
    """Test the full output pipeline."""
    df = pd.DataFrame({"time": [1, 2, 3], "residual": [0.1, 0.2, 0.3]})
    output_csv = os.path.join(temp_dirs["processed"], "cleaned_slr_data.csv")
    
    run_output_pipeline(
        cleaned_df=df,
        raw_data_dir=temp_dirs["raw"],
        output_csv_path=output_csv,
        checksum_dir=temp_dirs["processed"]
    )
    
    # Verify CSV exists
    assert os.path.exists(output_csv)
    
    # Verify checksum file exists
    checksum_file = os.path.join(temp_dirs["processed"], ".checksums.json")
    assert os.path.exists(checksum_file)
    
    # Verify content of checksum file
    with open(checksum_file, "r") as f:
        data = json.load(f)
    
    assert "cleaned_slr_data.csv" in data
    assert data["cleaned_slr_data.csv"]["file"] == "cleaned_slr_data.csv"
    assert len(data["cleaned_slr_data.csv"]["sha256"]) == 64
    
    # Verify raw data is still there
    assert os.path.exists(os.path.join(temp_dirs["raw"], "dummy_raw.txt"))