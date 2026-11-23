import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.ingestion import accumulate_streaming_stats, RunningStats

def test_running_stats_basic():
    """Test basic functionality of RunningStats class."""
    columns = ["A", "B"]
    stats = RunningStats(columns)

    # Chunk 1
    chunk1 = pd.DataFrame({"A": [1.0, 2.0, np.nan], "B": [10.0, 20.0, 30.0]})
    stats.update(chunk1)

    assert stats.count == 3
    assert stats.running_sums["A"] == 3.0
    assert stats.running_valid_counts["A"] == 2
    assert stats.running_sums["B"] == 60.0
    assert stats.running_valid_counts["B"] == 3

    # Chunk 2
    chunk2 = pd.DataFrame({"A": [3.0, 4.0], "B": [np.nan, 40.0]})
    stats.update(chunk2)

    assert stats.count == 5
    assert stats.running_sums["A"] == 10.0 # 1+2+3+4
    assert stats.running_valid_counts["A"] == 4
    assert stats.running_sums["B"] == 100.0 # 10+20+30+40
    assert stats.running_valid_counts["B"] == 4

    final_stats = stats.get_stats()
    assert final_stats["total_rows_processed"] == 5
    assert abs(final_stats["means"]["A"] - 2.5) < 1e-6
    assert abs(final_stats["means"]["B"] - 25.0) < 1e-6

def test_accumulate_streaming_stats_with_generator():
    """Test accumulate_streaming_stats with a generator of DataFrames."""
    def data_gen():
        yield pd.DataFrame({"A": [1.0, 2.0], "B": [10.0, 20.0]})
        yield pd.DataFrame({"A": [3.0, 4.0], "B": [30.0, 40.0]})

    stats = accumulate_streaming_stats(data_gen(), columns=["A", "B"])

    assert stats["total_rows_processed"] == 4
    assert abs(stats["means"]["A"] - 2.5) < 1e-6
    assert abs(stats["means"]["B"] - 25.0) < 1e-6
    assert stats["null_counts"]["A"] == 0
    assert stats["null_counts"]["B"] == 0

def test_accumulate_streaming_stats_with_nulls():
    """Test accumulate_streaming_stats with null values."""
    def data_gen():
        yield pd.DataFrame({"A": [1.0, np.nan], "B": [10.0, 20.0]})
        yield pd.DataFrame({"A": [3.0, 4.0], "B": [np.nan, 40.0]})

    stats = accumulate_streaming_stats(data_gen(), columns=["A", "B"])

    assert stats["total_rows_processed"] == 4
    assert abs(stats["means"]["A"] - 2.666666) < 1e-4 # (1+3+4)/3
    assert abs(stats["means"]["B"] - 23.333333) < 1e-4 # (10+20+40)/3
    assert stats["null_counts"]["A"] == 1
    assert stats["null_counts"]["B"] == 1

def test_verify_against_sample_csv(tmp_path):
    """Verify stats against a known sample CSV file."""
    # Create a test sample CSV
    sample_data = {
        "rolling temperature": [100.0, 200.0, 300.0, np.nan],
        "grain size": [10.0, 20.0, np.nan, 40.0],
        "Mg": [1.0, 2.0, 3.0, 4.0],
        "Si": [0.5, 0.6, 0.7, 0.8],
        "Cu": [0.1, 0.2, 0.3, 0.4],
        "Al": [98.4, 97.2, 96.0, 94.8]
    }
    df = pd.DataFrame(sample_data)
    csv_path = tmp_path / "test_sample.csv"
    df.to_csv(csv_path, index=False)

    # Load and compute stats
    chunks = pd.read_csv(csv_path, chunksize=2)
    stats = accumulate_streaming_stats(chunks, columns=list(sample_data.keys()))

    # Verify manually
    # rolling temperature: (100+200+300)/3 = 200
    # grain size: (10+20+40)/3 = 23.333
    # Mg: (1+2+3+4)/4 = 2.5
    # Si: (0.5+0.6+0.7+0.8)/4 = 0.65
    # Cu: (0.1+0.2+0.3+0.4)/4 = 0.25
    # Al: (98.4+97.2+96.0+94.8)/4 = 96.6

    assert stats["total_rows_processed"] == 4
    assert abs(stats["means"]["rolling temperature"] - 200.0) < 1e-6
    assert abs(stats["means"]["grain size"] - 23.333333) < 1e-4
    assert abs(stats["means"]["Mg"] - 2.5) < 1e-6
    assert abs(stats["means"]["Si"] - 0.65) < 1e-6
    assert abs(stats["means"]["Cu"] - 0.25) < 1e-6
    assert abs(stats["means"]["Al"] - 96.6) < 1e-6

    assert stats["null_counts"]["rolling temperature"] == 1
    assert stats["null_counts"]["grain size"] == 1
    assert stats["null_counts"]["Mg"] == 0
    assert stats["null_counts"]["Si"] == 0
    assert stats["null_counts"]["Cu"] == 0
    assert stats["null_counts"]["Al"] == 0