"""
Unit tests for the download and sampling logic in code/data/download.py.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
# Note: We assume the import path matches the project structure defined in API surface
from data.download import subset_csv


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with mock data for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a dataset with known distribution for outcome and species
        data = {
            'id': range(100),
            'outcome': ['saved', 'sacrificed'] * 50,  # Balanced
            'species': ['human', 'pet', 'animal'] * 33 + ['human'],  # Roughly balanced
            'value': range(100)
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def small_csv_file():
    """Create a small CSV file (fewer rows than target)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = {
            'id': range(10),
            'outcome': ['saved', 'sacrificed'] * 5,
            'species': ['human', 'pet'] * 5,
            'value': range(10)
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
        os.unlink(f.name)


def test_subset_csv_creates_file(temp_csv_file):
    """Test that subset_csv creates the output file."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
        out_path = out_f.name
        os.unlink(out_path)  # Remove the temp file, let function create it

    try:
        result_path = subset_csv(
            input_path=Path(temp_csv_file),
            output_path=Path(out_path),
            max_rows=50,
            seed=42,
            stratify_cols=['outcome', 'species']
        )

        assert result_path.exists()
        assert result_path == Path(out_path)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_subset_csv_correct_count(temp_csv_file):
    """Test that the output has the correct number of rows."""
    target_rows = 40
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
        out_path = out_f.name
        os.unlink(out_path)

    try:
        result_path = subset_csv(
            input_path=Path(temp_csv_file),
            output_path=Path(out_path),
            max_rows=target_rows,
            seed=42,
            stratify_cols=['outcome', 'species']
        )

        df_result = pd.read_csv(result_path)
        assert len(df_result) == target_rows
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_subset_csv_stratification(temp_csv_file):
    """Test that stratification columns preserve distribution."""
    target_rows = 50
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
        out_path = out_f.name
        os.unlink(out_path)

    try:
        subset_csv(
            input_path=Path(temp_csv_file),
            output_path=Path(out_path),
            max_rows=target_rows,
            seed=42,
            stratify_cols=['outcome', 'species']
        )

        df_result = pd.read_csv(out_path)

        # Check that all expected categories are present
        assert 'saved' in df_result['outcome'].values
        assert 'sacrificed' in df_result['outcome'].values
        assert len(df_result['species'].unique()) > 0
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_subset_csv_small_dataset(small_csv_file):
    """Test that subset_csv handles datasets smaller than max_rows."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
        out_path = out_f.name
        os.unlink(out_path)

    try:
        # Request more rows than available
        result_path = subset_csv(
            input_path=Path(small_csv_file),
            output_path=Path(out_path),
            max_rows=1000,  # Much larger than 10
            seed=42
        )

        df_result = pd.read_csv(result_path)
        # Should return all available rows (10)
        assert len(df_result) == 10
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)
