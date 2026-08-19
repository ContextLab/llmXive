import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Add code to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.generate_outputs import count_valid_observations, generate_exclusion_summary

@pytest.fixture
def sample_df():
    data = {
        "species_name": ["A", "A", "A", "A", "B", "B", "C", "C", "C", "C", "C"],
        "latitude": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "longitude": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "N": [10, 10, 10, 10, 20, 20, 30, 30, 30, 30, 30],
        "P": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "K": [5, 5, 5, 5, 6, 6, 7, 7, 7, 7, 7],
        "pH": [6, 6, 6, 6, 7, 7, 8, 8, 8, 8, 8],
        "root_depth": [10, 10, 10, 10, 20, 20, 30, 30, 30, 30, 30],
        "root_mass": [5, 5, 5, 5, 6, 6, 7, 7, 7, 7, 7]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_with_nulls():
    data = {
        "species_name": ["A", "A", "A", "A", "B", "B", "C", "C", "C", "C", "C"],
        "latitude": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "longitude": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "N": [10, 10, None, 10, 20, 20, 30, 30, 30, 30, 30],
        "P": [1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3],
        "K": [5, 5, 5, 5, 6, 6, 7, 7, 7, 7, 7],
        "pH": [6, 6, 6, 6, 7, 7, 8, 8, 8, 8, 8],
        "root_depth": [10, 10, 10, 10, 20, 20, 30, 30, 30, 30, 30],
        "root_mass": [5, 5, 5, 5, 6, 6, 7, 7, 7, 7, 7]
    }
    return pd.DataFrame(data)

def test_count_valid_observations_all_valid(sample_df):
    counts = count_valid_observations(sample_df)
    assert counts["A"] == 4
    assert counts["B"] == 2
    assert counts["C"] == 5

def test_count_valid_observations_with_nulls(sample_df_with_nulls):
    counts = count_valid_observations(sample_df_with_nulls)
    # Species A has one row with null N, so only 3 valid
    assert counts["A"] == 3
    assert counts["B"] == 2
    assert counts["C"] == 5

def test_generate_exclusion_summary(sample_df):
    counts = pd.Series({"A": 4, "B": 2, "C": 5})
    summary = generate_exclusion_summary(counts, threshold=10)
    
    assert len(summary) == 3
    assert set(summary["species_name"]) == {"A", "B", "C"}
    assert all(summary["reason"] == "observation_count < 10")
    assert summary[summary["species_name"] == "A"]["observation_count"].values[0] == 4

def test_generate_exclusion_summary_empty(sample_df):
    counts = pd.Series({"A": 15, "B": 20})
    summary = generate_exclusion_summary(counts, threshold=10)
    assert len(summary) == 0

def test_generate_exclusion_summary_file_output(sample_df):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_summary.csv"
        counts = pd.Series({"A": 4, "B": 2})
        generate_exclusion_summary(counts, threshold=10, output_path=output_path)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "species_name" in df.columns
        assert "observation_count" in df.columns
        assert "reason" in df.columns