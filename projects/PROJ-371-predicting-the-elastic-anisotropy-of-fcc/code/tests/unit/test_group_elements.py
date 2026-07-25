"""
Unit tests for the group_elements module.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.data.group_elements import (
    load_cleaned_data,
    build_element_groups,
    save_element_groups,
    group_elements_pipeline,
    parse_formula_simple
)
from src.utils.config import get_path


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        "formula": ["Fe", "Cu", "Fe2O3", "Al", "CuAl2", "NiFe"],
        "material_id": ["MP-1", "MP-2", "MP-3", "MP-4", "MP-5", "MP-6"],
        "C11": [200, 150, 250, 100, 180, 220],
        "C12": [100, 50, 120, 40, 80, 110],
        "C44": [80, 40, 90, 30, 70, 85],
        "A1": [1.6, 1.33, 1.5, 1.5, 1.75, 1.65]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestParseFormula:
    def test_simple_element(self):
        assert parse_formula_simple("Fe") == {"Fe"}

    def test_compound(self):
        result = parse_formula_simple("Fe2O3")
        assert "Fe" in result
        assert "O" in result
        assert len(result) == 2

    def test_complex_formula(self):
        result = parse_formula_simple("CuAl2")
        assert result == {"Cu", "Al"}

    def test_invalid_input(self):
        assert parse_formula_simple(None) == set()
        assert parse_formula_simple(123) == set()
        assert parse_formula_simple("") == set()


class TestLoadCleanedData:
    def test_load_valid_csv(self, temp_csv_file):
        df = load_cleaned_data(temp_csv_file)
        assert len(df) == 6
        assert "formula" in df.columns
        assert "material_id" in df.columns

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_cleaned_data("/nonexistent/path/file.csv")

    def test_missing_columns_raises(self, temp_output_dir):
        csv_path = os.path.join(temp_output_dir, "bad.csv")
        pd.DataFrame({"bad_col": [1]}).to_csv(csv_path, index=False)
        with pytest.raises(ValueError):
            load_cleaned_data(csv_path)

    def test_handles_nulls(self, temp_output_dir):
        data = {
            "formula": ["Fe", None, "Cu"],
            "material_id": ["MP-1", "MP-2", None]
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(temp_output_dir, "nulls.csv")
        df.to_csv(csv_path, index=False)

        result_df = load_cleaned_data(csv_path)
        # Should drop rows with nulls in key columns
        assert len(result_df) == 1
        assert result_df.iloc[0]["formula"] == "Fe"


class TestBuildElementGroups:
    def test_basic_grouping(self, sample_dataframe):
        groups = build_element_groups(sample_dataframe)

        assert "Fe" in groups
        assert "Cu" in groups
        assert "O" in groups
        assert "Al" in groups

        # Check specific memberships
        assert "MP-1" in groups["Fe"]
        assert "MP-3" in groups["Fe"]
        assert "MP-6" in groups["Fe"]
        assert "MP-2" in groups["Cu"]
        assert "MP-5" in groups["Cu"]
        assert "MP-4" in groups["Al"]
        assert "MP-5" in groups["Al"]

    def test_duplicate_elements_in_formula(self):
        # Formula like "FeFe" should still just result in {"Fe"}
        data = {
            "formula": ["FeFe"],
            "material_id": ["MP-1"]
        }
        df = pd.DataFrame(data)
        groups = build_element_groups(df)
        assert groups["Fe"] == ["MP-1"]

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["formula", "material_id"])
        groups = build_element_groups(df)
        assert groups == {}


class TestSaveElementGroups:
    def test_save_and_load(self, temp_output_dir):
        groups = {"Fe": ["MP-1", "MP-2"], "Cu": ["MP-3"]}
        output_path = os.path.join(temp_output_dir, "groups.json")

        saved = save_element_groups(groups, output_path)
        assert os.path.exists(saved)

        with open(saved, 'r') as f:
            loaded = json.load(f)

        assert loaded == groups

    def test_creates_directories(self, temp_output_dir):
        groups = {"Fe": ["MP-1"]}
        nested_path = os.path.join(temp_output_dir, "sub", "groups.json")

        saved = save_element_groups(groups, nested_path)
        assert os.path.exists(saved)


class TestGroupElementsPipeline:
    def test_full_pipeline(self, temp_csv_file, temp_output_dir):
        output_path = os.path.join(temp_output_dir, "result.json")
        result = group_elements_pipeline(temp_csv_file, output_path)

        assert os.path.exists(result)
        with open(result, 'r') as f:
            data = json.load(f)

        assert "Fe" in data
        assert "Cu" in data

    def test_pipeline_uses_defaults(self, temp_csv_file, monkeypatch, temp_output_dir):
        # Mock get_path to return our temp dir
        def mock_get_path(key, sub=None):
            if key == "data_processed":
                return Path(temp_output_dir)
            return Path(temp_output_dir)

        monkeypatch.setattr("src.data.group_elements.get_path", mock_get_path)

        # We need to ensure the input file is found, so we pass it explicitly
        # The output path should default to temp_output_dir/element_groups.json
        result = group_elements_pipeline(temp_csv_file)
        assert os.path.exists(result)


class TestMainFunction:
    @patch('src.data.group_elements.group_elements_pipeline')
    def test_main_success(self, mock_pipeline, temp_csv_file, temp_output_dir):
        mock_pipeline.return_value = os.path.join(temp_output_dir, "out.json")
        exit_code = main()
        assert exit_code == 0

    @patch('src.data.group_elements.load_cleaned_data')
    def test_main_file_not_found(self, mock_load, temp_output_dir):
        mock_load.side_effect = FileNotFoundError("Not found")
        exit_code = main()
        assert exit_code == 1