"""
Unit tests for bound_verifier.py (T031).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path

from src.services.bound_verifier import verify_bound_for_level, run_bound_verification, BOUND_THRESHOLD

def test_verify_bound_perfect():
    """Test case where all samples satisfy the bound."""
    data = {
        'predicted_gap': [0.05, 0.09, 0.01],
        'actual_gap': [0.05, 0.09, 0.01],
        'quantization_level': ['INT4', 'INT4', 'INT4']
    }
    df = pd.DataFrame(data)
    result = verify_bound_for_level(df, 'INT4')

    assert result['total_samples'] == 3
    assert result['samples_satisfying_bound'] == 3
    assert result['percentage_satisfying'] == 100.0
    assert result['status'] == 'verified'

def test_verify_bound_partial():
    """Test case where some samples satisfy the bound."""
    # 0.05 diff satisfies (< 0.1), 0.15 diff fails (>= 0.1)
    data = {
        'predicted_gap': [0.05, 0.15, 0.01],
        'actual_gap': [0.05, 0.30, 0.01],
        'quantization_level': ['INT4', 'INT4', 'INT4']
    }
    df = pd.DataFrame(data)
    result = verify_bound_for_level(df, 'INT4')

    assert result['total_samples'] == 3
    assert result['samples_satisfying_bound'] == 2
    assert abs(result['percentage_satisfying'] - 66.666) < 0.1
    assert result['status'] == 'verified'

def test_verify_bound_missing_level():
    """Test case where the level does not exist in the dataframe."""
    data = {
        'predicted_gap': [0.05],
        'actual_gap': [0.05],
        'quantization_level': ['INT8']
    }
    df = pd.DataFrame(data)
    result = verify_bound_for_level(df, 'INT4')

    assert result['total_samples'] == 0
    assert result['status'] == 'skipped'

def test_run_verification_integration():
    """Integration test for run_bound_verification with a temporary file."""
    data = {
        'predicted_gap': [0.05, 0.15, 0.05, 0.05, 0.05],
        'actual_gap': [0.05, 0.30, 0.05, 0.05, 0.05],
        'quantization_level': ['INT4', 'INT4', 'INT8', 'FP8', 'INT4']
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_input.parquet"
        output_path = Path(tmpdir) / "test_output.json"

        df.to_parquet(input_path)

        report = run_bound_verification(input_path=input_path, output_path=output_path)

        assert report['total_samples_analyzed'] == 5
        assert report['total_samples_satisfying_bound'] == 4 # Only 0.15 diff fails
        assert report['overall_percentage_satisfying'] == 80.0
        assert output_path.exists()

        # Verify JSON content
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert loaded['bound_threshold'] == BOUND_THRESHOLD
            assert len(loaded['level_breakdown']) == 3 # INT4, INT8, FP8

def test_run_verification_missing_file():
    """Test that run_bound_verification raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        run_bound_verification(input_path=Path("non_existent_file.parquet"))