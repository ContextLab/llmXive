"""
Unit tests for results_writer module.
"""
import os
import tempfile
import pytest
import pandas as pd
from code.results_writer import write_raw_evaluations, append_raw_evaluations, RAW_EVALUATION_COLUMNS

def test_write_raw_evaluations_creates_file():
    """Test that write_raw_evaluations creates the file with correct columns."""
    results = [
        {"dataset_id": 1, "model_name": "LR", "fold_id": 0, "repeat_id": 0, "accuracy": 0.9, "f1_score": 0.8},
        {"dataset_id": 1, "model_name": "LR", "fold_id": 1, "repeat_id": 0, "accuracy": 0.85, "f1_score": 0.75}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.csv")
        write_raw_evaluations(results, output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        
        assert list(df.columns) == RAW_EVALUATION_COLUMNS
        assert len(df) == 2

def test_write_raw_evaluations_empty_list():
    """Test that write_raw_evaluations handles empty list gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.csv")
        write_raw_evaluations([], output_path)
        
        assert not os.path.exists(output_path)

def test_write_raw_evaluations_missing_columns():
    """Test that write_raw_evaluations raises error on missing columns."""
    results = [{"dataset_id": 1}]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.csv")
        with pytest.raises(ValueError):
            write_raw_evaluations(results, output_path)

def test_append_raw_evaluations():
    """Test appending to existing file."""
    results1 = [
        {"dataset_id": 1, "model_name": "LR", "fold_id": 0, "repeat_id": 0, "accuracy": 0.9, "f1_score": 0.8}
    ]
    results2 = [
        {"dataset_id": 1, "model_name": "LR", "fold_id": 1, "repeat_id": 0, "accuracy": 0.85, "f1_score": 0.75}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.csv")
        
        write_raw_evaluations(results1, output_path)
        append_raw_evaluations(results2, output_path)
        
        df = pd.read_csv(output_path)
        assert len(df) == 2