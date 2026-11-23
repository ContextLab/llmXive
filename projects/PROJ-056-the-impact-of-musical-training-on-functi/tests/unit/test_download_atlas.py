import os
import pytest
import hashlib
from pathlib import Path
import pandas as pd

from code.analysis.download_atlas import download_file, verify_file_hash, parse_labels_file, create_parquet_atlas, ATLAS_OUTPUT_PATH, EXPECTED_CSV_SHA256

# Note: In a real test environment, we might mock the download or use a local fixture.
# For this task, we assume the download process runs or a fixture is provided.
# We will test the verification and parsing logic which is deterministic given a file.

@pytest.fixture
def mock_csv_file(tmp_path):
    """Creates a mock CSV file that mimics the Schaefer format."""
    csv_content = """#17Networks\tROIs\tLabels
    1\t1\tVisual_1
    1\t2\tVisual_1
    2\t3\tSomMot_1
    2\t4\tSomMot_1
    3\t5\tDorsAttn_1
    3\t6\tDorsAttn_1
    """
    file_path = tmp_path / "schaefer_mock.csv"
    file_path.write_text(csv_content)
    return file_path

def test_verify_file_hash(mock_csv_file):
    """Tests the hash verification logic."""
    # Calculate actual hash
    sha256_hash = hashlib.sha256()
    with open(mock_csv_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    actual_hash = sha256_hash.hexdigest()

    # Test positive case
    assert verify_file_hash(mock_csv_file, actual_hash) is True

    # Test negative case
    assert verify_file_hash(mock_csv_file, "wrong_hash") is False

def test_parse_labels_file(mock_csv_file):
    """Tests the CSV parsing logic."""
    df = parse_labels_file(mock_csv_file)
    
    assert 'roi_index' in df.columns
    assert 'network' in df.columns
    assert 'label' in df.columns
    
    # Check 0-based indexing (original 1 -> 0)
    assert df.iloc[0]['roi_index'] == 0
    assert df.iloc[0]['network'] == '1'
    assert df.iloc[0]['label'] == 'Visual_1'

def test_parquet_creation(tmp_path, mock_csv_file):
    """Tests the conversion to Parquet."""
    output_path = tmp_path / "test_atlas.parquet"
    create_parquet_atlas(mock_csv_file, output_path)
    
    assert output_path.exists()
    
    # Verify content
    df = pd.read_parquet(output_path)
    assert len(df) == 6
    assert 'roi_index' in df.columns
    assert 'network' in df.columns

def test_atlas_output_exists():
    """
    Integration-style check: Ensure the expected output path is valid.
    This test passes if the file exists after the main script runs.
    """
    # This test assumes the main script (or a fixture) has run to create the file.
    # In a CI/CD context, this would run after the download step.
    # We assert existence and valid parquet structure.
    if ATLAS_OUTPUT_PATH.exists():
        df = pd.read_parquet(ATLAS_OUTPUT_PATH)
        assert 'roi_index' in df.columns
        assert 'network' in df.columns
        assert len(df) > 0
    else:
        # If the file doesn't exist, we skip the check or fail depending on context.
        # For this task implementation, we assert existence to satisfy the requirement.
        # If the file is missing, the test fails, indicating the download task is incomplete.
        pytest.fail(f"Atlas file {ATLAS_OUTPUT_PATH} does not exist. Run download_atlas.py first.")
