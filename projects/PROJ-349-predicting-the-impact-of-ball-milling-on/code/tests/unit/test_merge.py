"""
Unit tests for the merge module (T015a).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.ingest.merge import (
    calculate_row_hash,
    merge_datasets,
    validate_traceability,
    process_flagged_entries,
    run_merge_pipeline,
    MIN_ROWS
)
from src.utils.exceptions import InsufficientDataError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def valid_mp_data(temp_dir):
    data = [
        {"experiment_id": "mp1", "source_id": "mp-123", "source_name": "Materials Project", "milling_speed": 500, "d50": 10.5},
        {"experiment_id": "mp2", "source_id": "mp-456", "source_name": "Materials Project", "milling_speed": 600, "d50": 12.0}
    ]
    path = temp_dir / "materials_project_raw.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return str(path)

@pytest.fixture
def valid_nist_data(temp_dir):
    data = [
        {"experiment_id": "nist1", "source_id": "nist-789", "source_name": "NIST", "milling_speed": 400, "d50": 8.2}
    ]
    path = temp_dir / "nist_raw.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return str(path)

@pytest.fixture
def valid_arxiv_data(temp_dir):
    data = [
        {"experiment_id": "arxiv1", "source_id": "2301.12345", "source_name": "arXiv", "milling_speed": 700, "d50": 15.0}
    ]
    path = temp_dir / "arxiv_tables.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return str(path)

@pytest.fixture
def insufficient_data(temp_dir):
    # Create only 2 rows total (below MIN_ROWS of 150)
    data = [
        {"experiment_id": "mp1", "source_id": "mp-123", "source_name": "Materials Project", "milling_speed": 500, "d50": 10.5},
        {"experiment_id": "mp2", "source_id": "mp-456", "source_name": "Materials Project", "milling_speed": 600, "d50": 12.0}
    ]
    path = temp_dir / "materials_project_raw.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    # Create empty nist and arxiv
    (temp_dir / "nist_raw.json").write_text("[]")
    (temp_dir / "arxiv_tables.json").write_text("[]")
    return str(path), str(temp_dir / "nist_raw.json"), str(temp_dir / "arxiv_tables.json")

def test_calculate_row_hash():
    row = pd.Series({"a": 1, "b": 2})
    hash1 = calculate_row_hash(row)
    row2 = pd.Series({"a": 1, "b": 2})
    hash2 = calculate_row_hash(row2)
    assert hash1 == hash2
    row3 = pd.Series({"a": 1, "b": 3})
    hash3 = calculate_row_hash(row3)
    assert hash1 != hash3

def test_merge_datasets_success(valid_mp_data, valid_nist_data, valid_arxiv_data):
    # Create a mock to satisfy the MIN_ROWS check by adding more rows
    # We need to inject enough rows to pass the < 150 check
    # Since we can't easily generate 150 rows in a test fixture without clutter,
    # we will patch the MIN_ROWS constant or the check logic.
    # However, the task requires the code to raise SystemExit if < 150.
    # So for a "success" test, we must provide enough data or mock the check.
    
    # Let's mock the MIN_ROWS check to 2 for this test to verify merging logic works
    with patch('src.ingest.merge.MIN_ROWS', 2):
        df, count = merge_datasets(valid_mp_data, valid_nist_data, valid_arxiv_data)
        assert count == 4 # 2 MP + 1 NIST + 1 ArXiv
        assert len(df) == 4
        assert 'source_name' in df.columns
        assert 'source_id' in df.columns

def test_merge_datasets_missing_files(temp_dir):
    # All files missing
    with patch('src.ingest.merge.MIN_ROWS', 0): # Allow 0 for this test
        with pytest.raises(SystemExit):
            merge_datasets("nonexistent.json", "nonexistent.json", "nonexistent.json")

def test_validate_traceability_filters_missing_ids():
    data = [
        {"source_name": "A", "source_id": "1", "val": 1},
        {"source_name": "B", "source_id": None, "val": 2}, # Missing ID
        {"source_name": None, "source_id": "3", "val": 3}, # Missing Name
        {"source_name": "C", "source_id": "4", "val": 4}
    ]
    df = pd.DataFrame(data)
    result = validate_traceability(df)
    assert len(result) == 2
    assert all(result['source_name'].notna())
    assert all(result['source_id'].notna())

def test_process_flagged_entries_disabled(temp_dir):
    # Create a minimal merged df
    merged_df = pd.DataFrame([{"source_name": "A", "source_id": "1", "val": 1}])
    
    # Create empty flagged file
    flagged_path = temp_dir / "flagged.json"
    flagged_path.write_text("[]")
    
    result = process_flagged_entries(merged_df, str(flagged_path), {"ocr_enabled": False})
    assert len(result) == 1

def test_run_merge_pipeline_success(valid_mp_data, valid_nist_data, valid_arxiv_data, temp_dir):
    output_path = str(temp_dir / "merged.parquet")
    
    # Mock MIN_ROWS to 2 to allow test to pass with small data
    with patch('src.ingest.merge.MIN_ROWS', 2):
        df = run_merge_pipeline(
            mp_path=valid_mp_data,
            nist_path=valid_nist_data,
            arxiv_path=valid_arxiv_data,
            output_path=output_path
        )
        
        assert len(df) == 4
        assert os.path.exists(output_path)
        
        # Verify parquet can be read back
        read_df = pd.read_parquet(output_path)
        assert len(read_df) == 4