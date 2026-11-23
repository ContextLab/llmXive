"""
Unit tests for streaming utilities.
"""
import os
import tempfile
import csv
import pytest
import numpy as np
from pathlib import Path

from code.utils.streaming_utils import (
    stream_csv_rows,
    OnlineStatsCalculator,
    compute_online_stats,
    stream_numeric_data,
    get_file_row_count
)


class TestStreamCsvRows:
    """Tests for the stream_csv_rows generator."""

    def test_stream_csv_rows_basic(self, tmp_path):
        """Test basic streaming of CSV rows."""
        file_path = tmp_path / "test.csv"
        data = [
            ["col1", "col2", "col3"],
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        rows = list(stream_csv_rows(str(file_path), chunk_size=2))
        
        assert len(rows) == 4  # header + 3 data rows
        assert rows[0] == ["col1", "col2", "col3"]
        assert rows[1] == ["1", "2", "3"]

    def test_stream_csv_rows_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            list(stream_csv_rows("nonexistent.csv"))

    def test_stream_csv_rows_empty_file(self, tmp_path):
        """Test handling of empty CSV file."""
        file_path = tmp_path / "empty.csv"
        file_path.touch()
        
        with pytest.raises(ValueError, match="CSV file is empty"):
            list(stream_csv_rows(str(file_path)))


class TestOnlineStatsCalculator:
    """Tests for Welford's online algorithm."""

    def test_basic_update(self):
        """Test basic mean and variance calculation."""
        calc = OnlineStatsCalculator(n_features=1)
        
        # Update with known values: [1, 2, 3, 4, 5]
        calc.update(np.array([[1], [2], [3], [4], [5]]))
        
        mean = calc.get_mean()
        var = calc.get_variance()
        
        assert np.isclose(mean[0], 3.0)
        assert np.isclose(var[0], 2.0)  # population variance

    def test_batch_update(self):
        """Test updating with a batch of data."""
        calc = OnlineStatsCalculator(n_features=2)
        
        data = np.array([
            [1, 10],
            [2, 20],
            [3, 30]
        ])
        calc.update(data)
        
        mean = calc.get_mean()
        assert np.isclose(mean[0], 2.0)
        assert np.isclose(mean[1], 20.0)

    def test_incremental_update(self):
        """Test incremental updates vs batch update."""
        calc1 = OnlineStatsCalculator(n_features=1)
        calc2 = OnlineStatsCalculator(n_features=1)
        
        # Incremental
        for val in [1, 2, 3, 4, 5]:
            calc1.update(np.array([[val]]))
        
        # Batch
        calc2.update(np.array([[1], [2], [3], [4], [5]]))
        
        assert np.allclose(calc1.get_mean(), calc2.get_mean())
        assert np.allclose(calc1.get_variance(), calc2.get_variance())

    def test_wrong_feature_count(self):
        """Test error when feature count mismatch."""
        calc = OnlineStatsCalculator(n_features=2)
        
        with pytest.raises(ValueError, match="Expected 2 features"):
            calc.update(np.array([[1]]))

    def test_std_calculation(self):
        """Test standard deviation calculation."""
        calc = OnlineStatsCalculator(n_features=1)
        calc.update(np.array([[1], [2], [3], [4], [5]]))
        
        std = calc.get_std()
        assert np.isclose(std[0], np.sqrt(2.0))


class TestComputeOnlineStats:
    """Tests for the compute_online_stats function."""

    def test_compute_stats_basic(self, tmp_path):
        """Test basic stats computation."""
        file_path = tmp_path / "stats_test.csv"
        data = [
            ["id", "value1", "value2"],
            ["1", "1.0", "10.0"],
            ["2", "2.0", "20.0"],
            ["3", "3.0", "30.0"],
            ["4", "4.0", "40.0"],
            ["5", "5.0", "50.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        stats, count = compute_online_stats(
            str(file_path),
            columns=["value1", "value2"]
        )
        
        assert count == 5
        assert "value1" in stats
        assert "value2" in stats
        assert np.isclose(stats["value1"]["mean"], 3.0)
        assert np.isclose(stats["value2"]["mean"], 30.0)

    def test_auto_detect_columns(self, tmp_path):
        """Test automatic detection of numeric columns."""
        file_path = tmp_path / "auto_detect.csv"
        data = [
            ["name", "value"],
            ["a", "1.0"],
            ["b", "2.0"],
            ["c", "3.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        stats, count = compute_online_stats(str(file_path))
        
        assert count == 3
        assert "value" in stats

    def test_missing_columns(self, tmp_path):
        """Test error when specified column is missing."""
        file_path = tmp_path / "missing_col.csv"
        data = [
            ["id", "value"],
            ["1", "1.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            compute_online_stats(str(file_path), columns=["nonexistent"])


class TestStreamNumericData:
    """Tests for the stream_numeric_data generator."""

    def test_stream_numeric_basic(self, tmp_path):
        """Test basic numeric data streaming."""
        file_path = tmp_path / "numeric.csv"
        data = [
            ["id", "val1", "val2"],
            ["1", "1.0", "10.0"],
            ["2", "2.0", "20.0"],
            ["3", "3.0", "30.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        chunks = list(stream_numeric_data(str(file_path), columns=["val1", "val2"]))
        
        assert len(chunks) == 1
        assert chunks[0].shape == (3, 2)
        assert np.isclose(chunks[0][0, 0], 1.0)

    def test_stream_numeric_auto_detect(self, tmp_path):
        """Test auto-detection of numeric columns."""
        file_path = tmp_path / "auto.csv"
        data = [
            ["name", "value"],
            ["a", "1.0"],
            ["b", "2.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        chunks = list(stream_numeric_data(str(file_path)))
        
        assert len(chunks) == 1
        assert chunks[0].shape == (2, 1)


class TestGetFileRowCount:
    """Tests for get_file_row_count function."""

    def test_count_rows(self, tmp_path):
        """Test row counting."""
        file_path = tmp_path / "count.csv"
        data = [
            ["id", "value"],
            ["1", "1.0"],
            ["2", "2.0"],
            ["3", "3.0"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        count = get_file_row_count(str(file_path))
        assert count == 3

    def test_count_empty_file(self, tmp_path):
        """Test counting in file with only header."""
        file_path = tmp_path / "header_only.csv"
        data = [
            ["id", "value"]
        ]
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        count = get_file_row_count(str(file_path))
        assert count == 0