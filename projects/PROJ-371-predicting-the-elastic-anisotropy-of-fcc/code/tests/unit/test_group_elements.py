"""
Unit tests for the element grouping functionality (T014b).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.data.group_elements import (
    parse_formula_simple,
    build_element_groups,
    load_cleaned_data,
    save_element_groups,
    group_elements_pipeline
)
from src.utils.config import get_path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        "material_id": ["MP-1", "MP-2", "MP-3", "MP-4"],
        "formula": ["Fe", "Ni", "Fe2O3", "AlCu"],
        "C11": [200, 250, 180, 150],
        "C12": [100, 120, 90, 80],
        "C44": [80, 90, 70, 60],
        "A1": [1.6, 1.8, 1.5, 1.7]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)

class TestParseFormula:
    """Tests for parse_formula_simple function."""

    def test_single_element(self):
        """Test parsing a single element formula."""
        result = parse_formula_simple("Fe")
        assert result == ["Fe"]

    def test_compound_with_numbers(self):
        """Test parsing a compound formula with stoichiometry."""
        result = parse_formula_simple("Fe2O3")
        assert result == ["Fe", "O"]

    def test_multiple_elements(self):
        """Test parsing a formula with multiple elements."""
        result = parse_formula_simple("AlCu")
        assert result == ["Al", "Cu"]

    def test_complex_formula(self):
        """Test parsing a complex formula."""
        result = parse_formula_simple("Ni3Al")
        assert result == ["Ni", "Al"]

    def test_empty_formula(self):
        """Test parsing an empty formula."""
        result = parse_formula_simple("")
        assert result == []

    def test_none_formula(self):
        """Test parsing a None formula."""
        result = parse_formula_simple(None)
        assert result == []

    def test_duplicate_elements_in_formula(self):
        """Test that duplicate elements in formula are deduplicated."""
        # This is an edge case, but should return unique elements
        result = parse_formula_simple("FeFe")
        assert result == ["Fe"]

class TestLoadCleanedData:
    """Tests for load_cleaned_data function."""

    def test_load_existing_file(self, temp_csv_file):
        """Test loading an existing CSV file."""
        df = load_cleaned_data(temp_csv_file)
        assert len(df) == 4
        assert "material_id" in df.columns
        assert "formula" in df.columns

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_cleaned_data("/nonexistent/path/file.csv")

    def test_load_empty_file(self):
        """Test that loading an empty file raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("material_id,formula\n")  # Header only
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_cleaned_data(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_missing_columns(self):
        """Test that loading a file with missing columns raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("material_id,C11\n")  # Missing formula column
            f.write("MP-1,200\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_cleaned_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestBuildElementGroups:
    """Tests for build_element_groups function."""

    def test_build_basic_groups(self, sample_dataframe):
        """Test building element groups from sample data."""
        groups = build_element_groups(sample_dataframe)

        assert "Fe" in groups
        assert "Ni" in groups
        assert "O" in groups
        assert "Al" in groups
        assert "Cu" in groups

        assert set(groups["Fe"]) == {"MP-1", "MP-3"}
        assert groups["Ni"] == ["MP-2"]
        assert groups["O"] == ["MP-3"]
        assert set(groups["Al"]) == {"MP-4"}
        assert groups["Cu"] == ["MP-4"]

    def test_build_empty_dataframe(self):
        """Test building groups from an empty DataFrame."""
        df = pd.DataFrame(columns=["material_id", "formula"])
        groups = build_element_groups(df)
        assert groups == {}

    def test_build_with_duplicate_elements(self):
        """Test that duplicate elements across materials are handled."""
        data = {
            "material_id": ["MP-1", "MP-2"],
            "formula": ["Fe", "Fe"]
        }
        df = pd.DataFrame(data)
        groups = build_element_groups(df)

        assert len(groups["Fe"]) == 2
        assert set(groups["Fe"]) == {"MP-1", "MP-2"}

class TestSaveElementGroups:
    """Tests for save_element_groups function."""

    def test_save_to_file(self, temp_output_dir):
        """Test saving element groups to a JSON file."""
        groups = {
            "Fe": ["MP-1", "MP-3"],
            "Ni": ["MP-2"],
            "O": ["MP-3"]
        }
        output_path = os.path.join(temp_output_dir, "test_groups.json")

        save_element_groups(groups, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            loaded_groups = json.load(f)

        assert loaded_groups == groups

    def test_save_creates_directories(self, temp_output_dir):
        """Test that save creates parent directories if needed."""
        groups = {"Fe": ["MP-1"]}
        nested_path = os.path.join(temp_output_dir, "subdir", "groups.json")

        save_element_groups(groups, nested_path)

        assert os.path.exists(nested_path)

class TestGroupElementsPipeline:
    """Tests for the full pipeline function."""

    def test_pipeline_end_to_end(self, temp_csv_file, temp_output_dir):
        """Test the full pipeline from CSV to JSON."""
        output_path = os.path.join(temp_output_dir, "element_groups.json")

        result = group_elements_pipeline(temp_csv_file, output_path)

        assert os.path.exists(output_path)
        assert isinstance(result, dict)
        assert "Fe" in result
        assert "Ni" in result

        with open(output_path, 'r') as f:
            saved_groups = json.load(f)

        assert saved_groups == result

    def test_pipeline_default_paths(self, sample_dataframe, temp_output_dir):
        """Test pipeline with default paths (using temp directory)."""
        # Create a CSV in temp directory
        csv_path = os.path.join(temp_output_dir, "cleaned_data.csv")
        sample_dataframe.to_csv(csv_path, index=False)

        # Mock get_path to return our temp directory
        with patch('src.data.group_elements.get_path') as mock_get_path:
            mock_get_path.side_effect = lambda section, filename: {
                ("data_processed", "elastic_anisotropy.csv"): csv_path,
                ("data_processed", "element_groups.json"): os.path.join(temp_output_dir, "element_groups.json")
            }[(section, filename)]

            result = group_elements_pipeline()

            assert result is not None
            assert "Fe" in result

class TestMainFunction:
    """Tests for the CLI main function."""

    def test_main_with_args(self, temp_csv_file, temp_output_dir, capsys):
        """Test main function with command line arguments."""
        output_path = os.path.join(temp_output_dir, "output.json")

        with patch('sys.argv', ['group_elements.py', '--input', temp_csv_file, '--output', output_path]):
            from src.data.group_elements import main
            main()

        assert os.path.exists(output_path)

    def test_main_with_verbose(self, temp_csv_file, temp_output_dir, capsys):
        """Test main function with verbose flag."""
        output_path = os.path.join(temp_output_dir, "output.json")

        with patch('sys.argv', ['group_elements.py', '--input', temp_csv_file, '--output', output_path, '--verbose']):
            from src.data.group_elements import main
            main()

        assert os.path.exists(output_path)
        captured = capsys.readouterr()
        # Should have some log output
        assert "Starting" in captured.out or "Starting" in captured.err
