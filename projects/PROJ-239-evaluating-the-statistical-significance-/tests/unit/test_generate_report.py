"""
Unit tests for the report generation script.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.generate_report import load_results, generate_table_markdown

@pytest.fixture
def sample_df():
    data = {
        'ICC': [0.0, 0.1, 0.2],
        'Alpha': [0.05, 0.05, 0.05],
        'Method': ['Naive', 'Naive', 'Naive'],
        'Empirical_Error_Rate': [0.051, 0.12, 0.25],
        'CI_Lower': [0.045, 0.10, 0.22],
        'CI_Upper': [0.057, 0.14, 0.28]
    }
    return pd.DataFrame(data)

def test_load_results_success(sample_df):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_df.to_csv(f.name, index=False)
        try:
            df = load_results(f.name)
            assert df.shape == sample_df.shape
            assert list(df.columns) == list(sample_df.columns)
        finally:
            os.unlink(f.name)

def test_load_results_missing_file():
    with pytest.raises(FileNotFoundError):
        load_results("non_existent_file.csv")

def test_load_results_missing_columns(sample_df):
    # Remove a required column
    bad_df = sample_df.drop(columns=['ICC'])
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        bad_df.to_csv(f.name, index=False)
        try:
            with pytest.raises(ValueError, match="missing required columns"):
                load_results(f.name)
        finally:
            os.unlink(f.name)

def test_generate_table_markdown(sample_df):
    md = generate_table_markdown(sample_df)
    assert isinstance(md, str)
    assert "ICC" in md
    assert "Naive" in md
    assert "0.051" in md