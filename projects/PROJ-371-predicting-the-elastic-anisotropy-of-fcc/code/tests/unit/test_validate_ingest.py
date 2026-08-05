import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Import the module under test
from src.data.validate_ingest import (
    load_ingest_results,
    verify_entry_count,
    validate_ingest,
    EXPECTED_COLUMNS
)

@pytest.fixture
def temp_mp_csv():
    """Create a temporary MP CSV file with valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'material_id': ['MP-1', 'MP-2'],
            'source': ['MP', 'MP'],
            'C11': [100.0, 150.0],
            'C12': [50.0, 60.0],
            'C44': [40.0, 50.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_aflow_csv():
    """Create a temporary AFLOW CSV file with valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'material_id': ['AFLOW-1', 'AFLOW-2'],
            'source': ['AFLOW', 'AFLOW'],
            'C11': [120.0, 160.0],
            'C12': [55.0, 65.0],
            'C44': [45.0, 55.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_empty_csv():
    """Create a temporary empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("material_id,source,C11,C12,C44\n")
        yield f.name
    os.unlink(f.name)

def test_load_ingest_results_both_sources(temp_mp_csv, temp_aflow_csv):
    """Test loading and merging results from both MP and AFLOW."""
    result = load_ingest_results(Path(temp_mp_csv), Path(temp_aflow_csv))
    
    assert len(result) == 4
    assert set(result['source'].unique()) == {'MP', 'AFLOW'}
    assert EXPECTED_COLUMNS.issubset(result.columns)

def test_load_ingest_results_only_mp(temp_mp_csv):
    """Test loading results from only MP source."""
    result = load_ingest_results(Path(temp_mp_csv), None)
    
    assert len(result) == 2
    assert all(result['source'] == 'MP')

def test_load_ingest_results_only_aflow(temp_aflow_csv):
    """Test loading results from only AFLOW source."""
    result = load_ingest_results(None, Path(temp_aflow_csv))
    
    assert len(result) == 2
    assert all(result['source'] == 'AFLOW')

def test_load_ingest_results_no_sources(temp_empty_csv):
    """Test that loading from no valid sources raises an error."""
    with pytest.raises(ValueError, match="No valid data sources found"):
        load_ingest_results(None, None)

def test_verify_entry_count_pass(temp_mp_csv):
    """Test entry count verification passes when threshold is met."""
    df = pd.read_csv(temp_mp_csv)
    assert verify_entry_count(df, min_entries=1) is True
    assert verify_entry_count(df, min_entries=2) is True

def test_verify_entry_count_fail(temp_mp_csv):
    """Test entry count verification fails when threshold is not met."""
    df = pd.read_csv(temp_mp_csv)
    assert verify_entry_count(df, min_entries=3) is False

def test_verify_entry_count_custom_threshold(temp_mp_csv):
    """Test entry count verification with custom threshold."""
    df = pd.read_csv(temp_mp_csv)
    assert verify_entry_count(df, min_entries=2) is True
    assert verify_entry_count(df, min_entries=5) is False

def test_validate_ingest_integration(temp_mp_csv, temp_aflow_csv):
    """Test the full validation pipeline with both sources."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
        output_path = out_f.name
    
    try:
        is_valid, df = validate_ingest(
            input_mp=temp_mp_csv,
            input_aflow=temp_aflow_csv,
            output_path=output_path,
            min_entries=3
        )
        
        assert is_valid is True
        assert len(df) == 4
        assert os.path.exists(output_path)
        
        # Verify saved file content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 4
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_validate_ingest_handles_missing_columns(temp_mp_csv):
    """Test that validation handles missing columns gracefully."""
    # Create a CSV with missing column
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'material_id': ['MP-1'],
            'C11': [100.0],
            'C12': [50.0]
            # Missing 'source' and 'C44'
        }
        pd.DataFrame(data).to_csv(f.name, index=False)
        temp_bad_csv = f.name
    
    try:
        # Should log warning but not crash
        is_valid, df = validate_ingest(
            input_mp=temp_mp_csv,
            input_aflow=temp_bad_csv,
            min_entries=1
        )
        # Should still work, though with warnings logged
        assert len(df) >= 1
    finally:
        os.unlink(temp_bad_csv)

def test_validate_ingest_empty_source(temp_empty_csv):
    """Test validation when one source is empty."""
    # Create a valid MP file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'material_id': ['MP-1'],
            'source': ['MP'],
            'C11': [100.0],
            'C12': [50.0],
            'C44': [40.0]
        }
        pd.DataFrame(data).to_csv(f.name, index=False)
        temp_valid_csv = f.name
    
    try:
        is_valid, df = validate_ingest(
            input_mp=temp_valid_csv,
            input_aflow=temp_empty_csv,
            min_entries=1
        )
        assert is_valid is True
        assert len(df) == 1
    finally:
        os.unlink(temp_valid_csv)