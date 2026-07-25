"""
Unit tests for the validate_ingest module.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.validate_ingest import (
    load_ingest_results,
    verify_entry_count,
    validate_ingest,
    MIN_UNIQUE_ENTRIES
)
from src.utils.config import get_path

@pytest.fixture
def temp_mp_csv(tmp_path):
    """Create a temporary MP ingestion CSV file."""
    data = {
        'material_id': ['MP-100', 'MP-101', 'MP-102'],
        'C11': [200, 210, 220],
        'C12': [100, 110, 120],
        'C44': [50, 60, 70]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "mp_elastic.csv"
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def temp_aflow_csv(tmp_path):
    """Create a temporary AFLOW ingestion CSV file."""
    data = {
        'material_id': ['AFLOW-200', 'AFLOW-201'],
        'C11': [180, 190],
        'C12': [90, 95],
        'C44': [40, 45]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "aflow_elastic.csv"
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def temp_empty_csv(tmp_path):
    """Create an empty CSV file."""
    file_path = tmp_path / "empty.csv"
    file_path.touch()
    return file_path

def test_load_ingest_results_both_sources(temp_mp_csv, temp_aflow_csv):
    """Test loading and merging from both MP and AFLOW."""
    df, skipped = load_ingest_results(temp_mp_csv, temp_aflow_csv)
    
    assert len(df) == 5  # 3 MP + 2 AFLOW
    assert 'source' in df.columns
    assert df['source'].tolist().count('materials_project') == 3
    assert df['source'].tolist().count('aflow') == 2
    assert 'material_id' in df.columns
    assert len(skipped) == 0

def test_load_ingest_results_only_mp(temp_mp_csv, tmp_path):
    """Test loading when only MP source exists."""
    non_existent = tmp_path / "non_existent.csv"
    df, skipped = load_ingest_results(temp_mp_csv, non_existent)
    
    assert len(df) == 3
    assert df['source'].tolist().count('materials_project') == 3
    assert len(skipped) == 0

def test_load_ingest_results_only_aflow(temp_aflow_csv, tmp_path):
    """Test loading when only AFLOW source exists."""
    non_existent = tmp_path / "non_existent.csv"
    df, skipped = load_ingest_results(non_existent, temp_aflow_csv)
    
    assert len(df) == 2
    assert df['source'].tolist().count('aflow') == 2
    assert len(skipped) == 0

def test_load_ingest_results_no_sources(tmp_path):
    """Test loading when no sources exist."""
    non_existent_1 = tmp_path / "no1.csv"
    non_existent_2 = tmp_path / "no2.csv"
    
    with pytest.raises(FileNotFoundError):
        load_ingest_results(non_existent_1, non_existent_2)

def test_verify_entry_count_pass():
    """Test verification when count meets threshold."""
    data = {
        'material_id': [f'MP-{i}' for i in range(MIN_UNIQUE_ENTRIES)]
    }
    df = pd.DataFrame(data)
    assert verify_entry_count(df, MIN_UNIQUE_ENTRIES) is True

def test_verify_entry_count_fail():
    """Test verification when count is below threshold."""
    data = {
        'material_id': [f'MP-{i}' for i in range(MIN_UNIQUE_ENTRIES - 1)]
    }
    df = pd.DataFrame(data)
    assert verify_entry_count(df, MIN_UNIQUE_ENTRIES) is False

def test_verify_entry_count_custom_threshold():
    """Test verification with custom threshold."""
    data = {
        'material_id': [f'MP-{i}' for i in range(10)]
    }
    df = pd.DataFrame(data)
    assert verify_entry_count(df, min_count=5) is True
    assert verify_entry_count(df, min_count=15) is False

def test_validate_ingest_integration(temp_mp_csv, temp_aflow_csv, tmp_path):
    """Test full validation pipeline."""
    output_path = tmp_path / "validated_output.csv"
    
    df = validate_ingest(temp_mp_csv, temp_aflow_csv, output_path)
    
    assert len(df) == 5
    assert output_path.exists()
    
    # Verify saved file content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 5
    assert 'source' in saved_df.columns
    assert 'material_id' in saved_df.columns

def test_validate_ingest_handles_missing_columns(temp_mp_csv, temp_aflow_csv, tmp_path):
    """Test validation when columns are missing."""
    # Create a file with missing column
    bad_path = tmp_path / "bad_aflow.csv"
    bad_data = {
        'material_id': ['AFLOW-999'],
        'C11': [200],
        # Missing C12, C44
    }
    pd.DataFrame(bad_data).to_csv(bad_path, index=False)
    
    output_path = tmp_path / "validated_bad.csv"
    
    # Should not raise, but should log warning and drop bad rows
    df = validate_ingest(temp_mp_csv, bad_path, output_path)
    
    # Should only have the valid MP rows (3)
    assert len(df) == 3

def test_validate_ingest_empty_source(temp_empty_csv, temp_mp_csv, tmp_path):
    """Test validation when one source is empty."""
    output_path = tmp_path / "validated_empty.csv"
    
    df = validate_ingest(temp_mp_csv, temp_empty_csv, output_path)
    
    # Should only have MP rows
    assert len(df) == 3
    assert output_path.exists()