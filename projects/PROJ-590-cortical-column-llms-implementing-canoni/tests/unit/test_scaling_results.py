"""
Unit tests for scaling results aggregation.
"""
import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import sys

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.experiments.scaling import ScalingResult, write_scaling_results

@pytest.fixture
def sample_results():
    return [
        ScalingResult(column_count=1, params=1000, mae=0.1, time_sec=10.0),
        ScalingResult(column_count=2, params=2000, mae=0.08, time_sec=20.0),
        ScalingResult(column_count=4, params=4000, mae=0.06, time_sec=40.0),
    ]

def test_write_scaling_results_creates_file(sample_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "scaling_law.csv")
        write_scaling_results(sample_results, output_file)
        
        assert os.path.exists(output_file)
        df = pd.read_csv(output_file)
        
        assert "columns" in df.columns
        assert "params" in df.columns
        assert "mae" in df.columns
        assert "time_sec" in df.columns
        
        assert len(df) == 3
        assert df.iloc[0]["columns"] == 1
        assert df.iloc[2]["mae"] == 0.06

def test_write_scaling_results_empty_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "scaling_law.csv")
        with pytest.raises(ValueError):
            write_scaling_results([], output_file)

def test_write_scaling_results_verification(sample_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "scaling_law.csv")
        # This should pass verification
        write_scaling_results(sample_results, output_file)
        
        # Verify content manually
        df = pd.read_csv(output_file)
        assert df["columns"].tolist() == [1, 2, 4]
        assert df["params"].tolist() == [1000, 2000, 4000]