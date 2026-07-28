"""
Unit tests for the row counting logic (T015b).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.ingest.count_rows import calculate_row_count, run_count_pipeline


@pytest.fixture
def temp_parquet_file():
    """Create a temporary parquet file with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        file_path = tmpdir_path / "test_merged.parquet"

        # Create a sample dataframe
        df = pd.DataFrame({
            "experiment_id": [1, 2, 3],
            "source": ["MP", "NIST", "arXiv"],
            "d50": [10.5, 20.0, 15.2]
        })
        df.to_parquet(file_path)
        yield file_path


@pytest.fixture
def temp_empty_parquet_file():
    """Create a temporary empty parquet file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        file_path = tmpdir_path / "test_empty.parquet"

        # Create an empty dataframe
        df = pd.DataFrame(columns=["experiment_id", "source", "d50"])
        df.to_parquet(file_path)
        yield file_path


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_calculate_row_count_success(temp_parquet_file, temp_output_dir):
    """Test successful row count calculation."""
    output_file = temp_output_dir / "row_count.json"

    count = calculate_row_count(temp_parquet_file, output_file)

    assert count == 3
    assert output_file.exists()

    with open(output_file, "r") as f:
        data = json.load(f)

    assert data["count"] == 3


def test_calculate_row_count_empty(temp_empty_parquet_file, temp_output_dir):
    """Test row count calculation on an empty dataset."""
    output_file = temp_output_dir / "row_count.json"

    count = calculate_row_count(temp_empty_parquet_file, output_file)

    assert count == 0
    assert output_file.exists()

    with open(output_file, "r") as f:
        data = json.load(f)

    assert data["count"] == 0


def test_calculate_row_count_file_not_found(temp_output_dir):
    """Test that FileNotFoundError is raised when input file is missing."""
    output_file = temp_output_dir / "row_count.json"
    missing_path = Path("/nonexistent/path/to/file.parquet")

    with pytest.raises(FileNotFoundError):
        calculate_row_count(missing_path, output_file)


def test_run_count_pipeline(temp_parquet_file, temp_output_dir):
    """Test the CLI entry point."""
    output_file = temp_output_dir / "row_count.json"

    count = run_count_pipeline(temp_parquet_file, output_file)

    assert count == 3
    assert output_file.exists()