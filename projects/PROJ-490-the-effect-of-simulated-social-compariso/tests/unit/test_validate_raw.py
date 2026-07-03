"""
Unit tests for code/data/validate_raw.py
"""
import os
import tempfile
import pytest
from pathlib import Path
import pandas as pd

import sys
# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.validate_raw import validate_raw_data_variables, REQUIRED_VARIABLES


@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory with a valid CSV file for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        valid_csv = tmp_path / "valid_data.csv"
        data = {
            "avatar_condition": [0, 1, 0, 1],
            "pre_self_esteem": [20.5, 22.1, 19.8, 23.0],
            "post_self_esteem": [21.0, 18.5, 20.1, 22.8],
            "comparison_tendency": [3.2, 4.1, 2.9, 3.8]
        }
        df = pd.DataFrame(data)
        df.to_csv(valid_csv, index=False)
        yield tmp_path


@pytest.fixture
def temp_csv_missing_var():
    """Create a temporary directory with a CSV missing a required variable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        invalid_csv = tmp_path / "invalid_data.csv"
        data = {
            "avatar_condition": [0, 1, 0],
            "pre_self_esteem": [20.5, 22.1, 19.8],
            # Missing post_self_esteem and comparison_tendency
        }
        df = pd.DataFrame(data)
        df.to_csv(invalid_csv, index=False)
        yield tmp_path


@pytest.fixture
def temp_csv_empty():
    """Create a temporary directory with an empty CSV file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        empty_csv = tmp_path / "empty_data.csv"
        empty_csv.write_text("")
        yield tmp_path


def test_validate_raw_data_variables_success(temp_csv_dir):
    """Test that a valid CSV passes validation."""
    csv_path = temp_csv_dir / "valid_data.csv"
    assert validate_raw_data_variables(csv_path) is True


def test_validate_raw_data_variables_missing_columns(temp_csv_missing_var):
    """Test that a CSV with missing columns returns False."""
    csv_path = temp_csv_missing_var / "invalid_data.csv"
    assert validate_raw_data_variables(csv_path) is False


def test_validate_raw_data_variables_file_not_found():
    """Test that a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_raw_data_variables(Path("/non/existent/file.csv"))


def test_validate_raw_data_variables_empty_file(temp_csv_empty):
    """Test that an empty CSV raises ValueError."""
    csv_path = temp_csv_empty / "empty_data.csv"
    with pytest.raises(ValueError):
        validate_raw_data_variables(csv_path)


def test_required_variables_set():
    """Verify the required variables set matches FR-009."""
    expected = {"avatar_condition", "pre_self_esteem", "post_self_esteem", "comparison_tendency"}
    assert REQUIRED_VARIABLES == expected
