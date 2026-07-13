"""
Tests for Metric Aggregation Module (T023)
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from metric_aggregation import aggregate_metrics, write_aggregate_csv, load_metrics_for_group
from logging_config import setup_logger

logger = setup_logger("test_metric_aggregation", "data/logs/test_metric_aggregation.log")


def test_aggregate_metrics_calculation():
    """Test that mean, median, and variance are calculated correctly."""
    data = {
        "cyclomatic_complexity": [1, 2, 3, 4, 5],
        "lines_of_code": [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    cols = ["cyclomatic_complexity"]
    result = aggregate_metrics(df, cols)
    
    assert "cyclomatic_complexity" in result
    assert result["cyclomatic_complexity"]["mean"] == 3.0
    assert result["cyclomatic_complexity"]["median"] == 3.0
    # Variance of [1,2,3,4,5] (sample) is 2.5
    assert np.isclose(result["cyclomatic_complexity"]["variance"], 2.5)
    assert result["cyclomatic_complexity"]["count"] == 5


def test_aggregate_metrics_with_nan():
    """Test that NaN values are handled correctly."""
    data = {
        "cyclomatic_complexity": [1.0, np.nan, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    cols = ["cyclomatic_complexity"]
    result = aggregate_metrics(df, cols)
    
    # Should ignore NaN
    assert result["cyclomatic_complexity"]["count"] == 4
    # Mean of [1, 3, 4, 5] is 3.25
    assert np.isclose(result["cyclomatic_complexity"]["mean"], 3.25)


def test_write_aggregate_csv(tmp_path):
    """Test writing aggregates to CSV."""
    aggregates = {
        "metric_a": {"mean": 10.0, "median": 10.0, "variance": 1.0, "count": 10},
        "metric_b": {"mean": 20.0, "median": 20.0, "variance": 2.0, "count": 20}
    }
    
    output_file = write_aggregate_csv("test_group", aggregates, tmp_path)
    
    assert output_file.exists()
    df = pd.read_csv(output_file)
    
    assert len(df) == 2
    assert "metric_name" in df.columns
    assert "mean" in df.columns
    assert "median" in df.columns
    assert "variance" in df.columns
    assert "count" in df.columns
    
    assert df.loc[df["metric_name"] == "metric_a", "mean"].values[0] == 10.0


def test_load_metrics_for_group_missing_file():
    """Test error handling when file is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        metrics_dir = Path(tmp_dir)
        with pytest.raises(FileNotFoundError):
            load_metrics_for_group("nonexistent", metrics_dir)
