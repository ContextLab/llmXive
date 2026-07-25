"""
Unit tests for the element grouping functionality (T014b).

Tests verify:
1. Loading cleaned data correctly
2. Building element groups from formulas
3. Saving element groups to JSON
4. End-to-end pipeline execution
5. Formula parsing integration
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.group_elements import (
    load_cleaned_data,
    build_element_groups,
    save_element_groups,
    group_elements_pipeline,
    main
)
from src.data.features import parse_formula


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with material IDs and formulas."""
    return pd.DataFrame({
        'material_id': ['MP-100', 'MP-101', 'MP-102', 'MP-103'],
        'formula': ['Al', 'Cu', 'AlCu', 'FeNi'],
        'C11': [100, 150, 120, 130],
        'C12': [50, 60, 55, 65],
        'C44': [30, 40, 35, 45],
        'A1': [0.6, 0.8, 0.7, 0.9]
    })


@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLoadCleanedData:
    """Tests for load_cleaned_data function."""

    def test_load_valid_csv(self, temp_csv_file, sample_dataframe):
        """Test loading a valid CSV file."""
        df = load_cleaned_data(temp_csv_file)
        assert len(df) == len(sample_dataframe)
        assert 'material_id' in df.columns
        assert 'formula' in df.columns
        assert list(df['material_id']) == list(sample_dataframe['material_id'])

    def test_missing_file_raises(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_cleaned_data(Path("/nonexistent/path/file.csv"))

    def test_missing_columns_raises(self, temp_output_dir):
        """Test that missing required columns raise ValueError."""
        invalid_df = pd.DataFrame({
            'C11': [100, 150],
            'C12': [50, 60]
        })
        invalid_path = temp_output_dir / "invalid.csv"
        invalid_df.to_csv(invalid_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_cleaned_data(invalid_path)


class TestBuildElementGroups:
    """Tests for build_element_groups function."""

    def test_single_element_materials(self, sample_dataframe):
        """Test grouping with single-element materials."""
        df = pd.DataFrame({
            'material_id': ['MP-100', 'MP-101'],
            'formula': ['Al', 'Cu']
        })
        groups = build_element_groups(df)

        assert 'Al' in groups
        assert 'Cu' in groups
        assert groups['Al'] == ['MP-100']
        assert groups['Cu'] == ['MP-101']

    def test_multi_element_materials(self, sample_dataframe):
        """Test grouping with multi-element materials."""
        df = pd.DataFrame({
            'material_id': ['MP-100', 'MP-101'],
            'formula': ['AlCu', 'FeNi']
        })
        groups = build_element_groups(df)

        assert 'Al' in groups
        assert 'Cu' in groups
        assert 'Fe' in groups
        assert 'Ni' in groups
        assert groups['Al'] == ['MP-100']
        assert groups['Cu'] == ['MP-100']
        assert groups['Fe'] == ['MP-101']
        assert groups['Ni'] == ['MP-101']

    def test_shared_elements(self, sample_dataframe):
        """Test that elements shared across materials are grouped correctly."""
        df = pd.DataFrame({
            'material_id': ['MP-100', 'MP-101', 'MP-102'],
            'formula': ['AlCu', 'AlFe', 'CuFe']
        })
        groups = build_element_groups(df)

        assert set(groups['Al']) == {'MP-100', 'MP-101'}
        assert set(groups['Cu']) == {'MP-100', 'MP-102'}
        assert set(groups['Fe']) == {'MP-101', 'MP-102'}

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['material_id', 'formula'])
        groups = build_element_groups(df)
        assert groups == {}

    def test_sorted_output(self, sample_dataframe):
        """Test that output lists are sorted."""
        df = pd.DataFrame({
            'material_id': ['MP-103', 'MP-101', 'MP-102'],
            'formula': ['Al', 'Al', 'Al']
        })
        groups = build_element_groups(df)

        assert groups['Al'] == ['MP-101', 'MP-102', 'MP-103']


class TestSaveElementGroups:
    """Tests for save_element_groups function."""

    def test_save_and_load_json(self, temp_output_dir):
        """Test saving element groups to JSON and loading back."""
        element_groups = {
            'Al': ['MP-100', 'MP-101'],
            'Cu': ['MP-102'],
            'Fe': ['MP-103', 'MP-104']
        }
        output_path = temp_output_dir / "element_groups.json"

        save_element_groups(element_groups, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            loaded_groups = json.load(f)

        assert loaded_groups == element_groups

    def test_creates_directories(self, temp_output_dir):
        """Test that save creates parent directories if needed."""
        element_groups = {'Al': ['MP-100']}
        nested_path = temp_output_dir / "subdir" / "element_groups.json"

        save_element_groups(element_groups, nested_path)

        assert nested_path.exists()


class TestGroupElementsPipeline:
    """Tests for the complete pipeline."""

    def test_pipeline_end_to_end(self, sample_dataframe, temp_output_dir):
        """Test the complete pipeline from input to output."""
        input_path = temp_output_dir / "cleaned_data.csv"
        output_path = temp_output_dir / "element_groups.json"
        sample_dataframe.to_csv(input_path, index=False)

        groups = group_elements_pipeline(input_path, output_path)

        assert len(groups) > 0
        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved_groups = json.load(f)

        assert saved_groups == groups

    def test_pipeline_with_complex_formulas(self, temp_output_dir):
        """Test pipeline with complex chemical formulas."""
        complex_data = pd.DataFrame({
            'material_id': ['MP-100', 'MP-101', 'MP-102'],
            'formula': ['Al', 'Cu3Au', 'FeNiCo']
        })
        input_path = temp_output_dir / "cleaned_data.csv"
        output_path = temp_output_dir / "element_groups.json"
        complex_data.to_csv(input_path, index=False)

        groups = group_elements_pipeline(input_path, output_path)

        assert 'Al' in groups
        assert 'Cu' in groups
        assert 'Au' in groups
        assert 'Fe' in groups
        assert 'Ni' in groups
        assert 'Co' in groups


class TestParseFormulaIntegration:
    """Integration tests for formula parsing within grouping."""

    def test_parse_formula_basic(self):
        """Test basic formula parsing."""
        elements = parse_formula("Al")
        assert elements == ['Al']

    def test_parse_formula_compound(self):
        """Test compound formula parsing."""
        elements = parse_formula("AlCu")
        assert set(elements) == {'Al', 'Cu'}

    def test_parse_formula_with_numbers(self):
        """Test formula parsing with stoichiometric numbers."""
        elements = parse_formula("Al2Cu3")
        assert set(elements) == {'Al', 'Cu'}

    def test_parse_formula_complex(self):
        """Test complex formula parsing."""
        elements = parse_formula("FeNiCoCrMn")
        assert set(elements) == {'Fe', 'Ni', 'Co', 'Cr', 'Mn'}

    def test_formula_parsing_in_grouping(self, sample_dataframe):
        """Test that formula parsing works correctly in the grouping context."""
        df = pd.DataFrame({
            'material_id': ['MP-100', 'MP-101'],
            'formula': ['Al2Cu3', 'FeNi']
        })
        groups = build_element_groups(df)

        assert set(groups['Al']) == {'MP-100'}
        assert set(groups['Cu']) == {'MP-100'}
        assert set(groups['Fe']) == {'MP-101'}
        assert set(groups['Ni']) == {'MP-101'}


class TestMainFunction:
    """Tests for the main entry point."""

    @patch('src.data.group_elements.get_path')
    @patch('src.data.group_elements.group_elements_pipeline')
    def test_main_success(self, mock_pipeline, mock_get_path, temp_output_dir):
        """Test successful main execution."""
        mock_get_path.side_effect = [
            temp_output_dir / "cleaned.csv",
            temp_output_dir / "groups.json"
        ]
        mock_pipeline.return_value = {'Al': ['MP-100']}

        exit_code = main()
        assert exit_code == 0

    @patch('src.data.group_elements.get_path')
    def test_main_file_not_found(self, mock_get_path, temp_output_dir):
        """Test main when input file is not found."""
        mock_get_path.return_value = temp_output_dir / "nonexistent.csv"

        exit_code = main()
        assert exit_code == 1

    @patch('src.data.group_elements.get_path')
    def test_main_value_error(self, mock_get_path, temp_output_dir):
        """Test main when data validation fails."""
        mock_get_path.return_value = temp_output_dir / "invalid.csv"

        # Create an invalid CSV
        invalid_df = pd.DataFrame({'C11': [100]})
        invalid_df.to_csv(temp_output_dir / "invalid.csv", index=False)

        exit_code = main()
        assert exit_code == 1
